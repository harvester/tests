import json
import shlex
import subprocess
from time import sleep
from operator import add
from functools import reduce
from datetime import datetime, timedelta

import pytest
import paramiko


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.networks",
    "harvester_e2e_tests.fixtures.virtualmachines",
    "harvester_e2e_tests.fixtures.images"
]

tcp = "sudo sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/g' /etc/ssh/sshd_config"
restore_tcp = "sudo sed -i 's/AllowTcpForwarding yes/AllowTcpForwarding no/g' /etc/ssh/sshd_config"
restart_ssh = "sudo systemctl restart sshd.service"

vm_credential = {"user": "opensuse", "password": "123456"}
node_user = "rancher"

cloud_user_data = \
    """
password: {password}\nchpasswd: {{ expire: False }}\nssh_pwauth: True
"""

cloud_network_data = \
    """
network:
  version: 1
  config:
    - type: physical
      name: eth0
      subnets:
        - type: dhcp
    - type: physical
      name: eth1
      subnets:
        - type: dhcp
"""


@pytest.fixture(scope="session")
def client():
    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    yield client
    client.close()


@pytest.fixture(scope='module')
def cluster_network(vlan_nic, api_client, unique_name):
    code, data = api_client.clusternetworks.get_config()
    assert 200 == code, (code, data)

    node_key = 'network.harvesterhci.io/matched-nodes'
    cnet_nodes = dict()  # cluster_network: items
    for cfg in data['items']:
        if vlan_nic in cfg['spec']['uplink']['nics']:
            nodes = json.loads(cfg['metadata']['annotations'][node_key])
            cnet_nodes.setdefault(cfg['spec']['clusterNetwork'], []).extend(nodes)

    code, data = api_client.hosts.get()
    assert 200 == code, (code, data)
    all_nodes = set(n['id'] for n in data['data'])
    try:
        # vlad_nic configured on specific cluster network, reuse it
        yield next(cnet for cnet, nodes in cnet_nodes.items() if all_nodes == set(nodes))
        return None
    except StopIteration:
        configured_nodes = reduce(add, cnet_nodes.values(), [])
        if any(n in configured_nodes for n in all_nodes):
            raise AssertionError(
                "Not all nodes' VLAN NIC {vlan_nic} are available.\n"
                f"VLAN NIC configured nodes: {configured_nodes}\n"
                f"All nodes: {all_nodes}\n"
            )

    # Create cluster network
    cnet = f"cnet-{datetime.strptime(unique_name, '%Hh%Mm%Ss%f-%m-%d').strftime('%H%M%S')}"
    created = []
    code, data = api_client.clusternetworks.create(cnet)
    assert 201 == code, (code, data)
    while all_nodes:
        node = all_nodes.pop()
        code, data = api_client.clusternetworks.create_config(node, cnet, vlan_nic, hostname=node)
        assert 201 == code, (
            f"Failed to create cluster config for {node}\n"
            f"Created: {created}\t Remaining: {all_nodes}\n"
            f"API Status({code}): {data}"
        )
        created.append(node)

    yield cnet

    # Teardown
    deleted = {name: api_client.clusternetworks.delete_config(name) for name in created}
    failed = [(name, code, data) for name, (code, data) in deleted.items() if 200 != code]
    if failed:
        fmt = "Unable to delete VLAN Config {} with error ({}): {}"
        raise AssertionError(
            "\n".join(fmt.format(name, code, data) for (name, code, data) in failed)
        )

    code, data = api_client.clusternetworks.delete(cnet)
    assert 200 == code, (code, data)


@pytest.fixture(scope="module")
def vm_network(api_client, unique_name, wait_timeout, cluster_network, vlan_id):
    code, data = api_client.networks.create(
        unique_name, vlan_id, cluster_network=cluster_network
    )
    assert 201 == code, (code, data)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.networks.get(unique_name)
        annotations = data['metadata'].get('annotations', {})
        if 200 == code and annotations.get('network.harvesterhci.io/route'):
            route = json.loads(annotations['network.harvesterhci.io/route'])
            if route['cidr']:
                break
        sleep(3)
    else:
        raise AssertionError(
            "VM network created but route info not available\n"
            f"API Status({code}): {data}"
        )

    yield dict(name=unique_name, cidr=route['cidr'], namespace=data['metadata']['namespace'])

    code, data = api_client.networks.delete(unique_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.networks.get(unique_name)
        if 404 == code:
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to remote VM network {unique_name} after {wait_timeout}s\n"
            f"API Status({code}): {data}"
        )


def create_image_url(api_client, display_name, image_url, wait_timeout):
    code, data = api_client.images.create_by_url(display_name, image_url)

    assert 201 == code, (code, data)
    image_spec = data.get('spec')

    assert display_name == image_spec.get('displayName')
    assert "download" == image_spec.get('sourceType')

    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        code, data = api_client.images.get(display_name)
        image_status = data.get('status', {})

        assert 200 == code, (code, data)
        if image_status.get('progress') == 100:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to download image {display_name} with {wait_timeout} timed out\n"
            f"Still got {code} with {data}"
        )


def check_vm_running(api_client, vm_name, wait_timeout):
    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        code, data = api_client.vms.get(vm_name)
        vm_fields = data['metadata']['fields']

        assert 200 == code, (code, data)
        if vm_fields[2] == 'Running':
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to create VM {vm_name} in Running status, exceed given timeout\n"
            f"Still got {code} with {data}"
        )


def check_vm_ip_exists(api_client, vm_name, wait_timeout):
    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
        if 'ipAddress' in data['status']['interfaces'][0]:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to get VM {vm_name} IP address, exceed the given timed out\n"
            f"Still got {code} with {data}"
        )


@pytest.mark.p0
@pytest.mark.networks
class TestBackendNetwork:

    @pytest.mark.p0
    @pytest.mark.networks
    def test_mgmt_network_connection(
        self, api_client, request, client, image_opensuse, unique_name, wait_timeout,
        host_shell, vm_shell_from_host, vm_checker
    ):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/validate-network-management-network/


        Steps:
        1. Create a new VM
        2. Make sure that the network is set to the management network with masquerade as the type
        3. Wait until the VM boot in running state
        4. Check can ping VM with management network from Harvester node
        5. Check can SSH to VM with management network from Harvester node
        6. Check can't SSH to VM with management network from external host
        """
        vip = request.config.getoption('--endpoint').strip('https://')
        vm_user, vm_passwd = vm_credential['user'], vm_credential['password']

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        # Update AllowTcpForwarding for ssh jumpstart

        spec = api_client.vms.Spec(1, 2)

        spec.user_data += cloud_user_data.format(password=vm_passwd)

        vm_name = unique_name + "-mgmt"
        # Create VM
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)

        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # Get VM interface ipAddresses
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        interfaces_data = data['status']['interfaces']

        assert 1 == len(interfaces_data), (
            f"Failed: get more than one interface: {interfaces_data}"
        )

        mgmt_ip = interfaces_data[0]['ipAddress']

        # Ping management ip address from Harvester node
        with host_shell.login(vip) as sh:
            stdout, stderr = sh.exec_command(f"ping -c 50 {mgmt_ip}")

        assert stdout.find(f"64 bytes from {mgmt_ip}") > 0, (
            f"Failed to ping VM management IP {mgmt_ip} "
            f"on management interface from Harvester node")

        # SSH to management ip address and execute command from Harvester node
        with vm_shell_from_host(vip, mgmt_ip, vm_user, vm_passwd) as sh:
            stdout, stderr = sh.exec_command("ls")

        assert stdout.find("bin") == 0, (
            f"Failed to ssh to VM management IP {mgmt_ip} "
            f"on management interface from Harvester node")

        # Check should not SSH to management ip address from external host
        command = ['/usr/bin/ssh', '-o', 'ConnectTimeout=5', mgmt_ip]

        with pytest.raises(subprocess.CalledProcessError) as ex:
            subprocess.check_output(command, stderr=subprocess.STDOUT,
                                    shell=False, encoding="utf-8")

        # OpenSSH returns the return code of the program that was executed on
        # the remote, unless there was an error for SSH itself, in which case
        # it returns 255
        assert ex.value.returncode == 255, ("Failed: should not be able to SSH"
                                            " to VM on management interface"
                                            f" {mgmt_ip} from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.p0
    @pytest.mark.networks
    @pytest.mark.dependency(name="vlan_network_connection")
    def test_vlan_network_connection(self, api_client, request, client, unique_name,
                                     image_opensuse, vm_network, wait_timeout, vm_checker):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/validate-network-external-vlan/


        Steps:
        1. Create an external VLAN network
        2. Create a new VM and set the external vlan network to it
        3. Check can ping external VLAN IP from external host
        4. Check can SSH to VM from external IP from external host
        """
        vm_name = unique_name + "-vlan"

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        spec = api_client.vms.Spec(1, 2, mgmt_network=False)
        spec.user_data += cloud_user_data.format(password=vm_credential["password"])

        # Create VM
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)

        spec.add_network("nic-1", f"{vm_network['namespace']}/{vm_network['name']}")

        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # Get VM interface ipAddresses
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        interfaces_data = data['status']['interfaces']

        assert 1 == len(interfaces_data), (
            f"Failed: get more than one interface: {interfaces_data}"
        )

        assert "nic-1" == interfaces_data[0]['name'], (
            f"Failed: Network name did not match to added vlan: {interfaces_data}"
        )

        vlan_ip = interfaces_data[0]['ipAddress']

        # Ping vlan ip address from external host
        command = ['/usr/bin/ping', '-c', '50', vlan_ip]

        result = subprocess.check_output(command, shell=False, encoding="utf-8")

        assert result.find(f"64 bytes from {vlan_ip}") > 0, (
            f"Failed to ping VM external vlan IP {vlan_ip} "
            f"on vlan interface from external host")

        # SSH to vlan ip address and execute command from external host
        _stdout, _stderr = self.ssh_client(
            client, vlan_ip, vm_credential["user"], vm_credential["password"], 'ls', wait_timeout)

        stdout = _stdout.read().decode('ascii').strip("\n")

        assert stdout.find("bin") == 0, (
            f"Failed to ssh to VM external vlan IP {vlan_ip}"
            f"on vlan interface from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.p0
    @pytest.mark.networks
    @pytest.mark.dependency(name="reboot_vlan_connection",
                            depends=["vlan_network_connection"])
    def test_reboot_vlan_connection(self, api_client, request, unique_name,
                                    image_opensuse, vm_network, wait_timeout, vm_checker):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/negative-vlan-after-reboot/


        Steps:
        1. Create an external VLAN network
        2. Create a new VM and add the external vlan network
        3. Check can ping external VLAN IP
        4. Reboot VM
        5. Ping VM during reboot
        6. Check can't ping VM during reboot
        7. Check the VM should reboot
        8. Ping VM after reboot
        9. Check can ping VM
        """
        vm_name = unique_name + "-reboot-vlan"

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        spec = api_client.vms.Spec(1, 2, mgmt_network=False)
        spec.user_data += cloud_user_data.format(password=vm_credential["password"])

        # Create VM
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)

        spec.add_network("nic-1", f"{vm_network['namespace']}/{vm_network['name']}")

        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # Get VM interface ipAddresses
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        interfaces_data = data['status']['interfaces']

        assert 1 == len(interfaces_data), (
            f"Failed: get more than one interface: {interfaces_data}"
        )

        assert "nic-1" == interfaces_data[0]['name'], (
            f"Failed: Network name did not match to added vlan: {interfaces_data}"
        )

        vlan_ip = interfaces_data[0]['ipAddress']

        # Check can ping vlan ip

        command = ['/usr/bin/ping', '-c', '10', vlan_ip]

        result = subprocess.check_output(command, shell=False, encoding="utf-8")

        assert result.find(f"64 bytes from {vlan_ip}") > 0, (
            f"Failed to ping VM external vlan IP {vlan_ip} "
            f"on vlan interface from external host")

        # Restart VM
        code, data = api_client.vms.restart(vm_name)
        assert 204 == code, (f"Failed to reboot vm with error: {code}, {data}")

        # Check VM start in Starting state
        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.vms.get(vm_name)
            assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
            vm_fields = data['metadata']['fields']

            if vm_fields[2] == 'Starting':
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to restart VM {vm_name} in Starting status, exceed given timeout\n"
                f"Still got {code} with {data}"
            )

        # Check can't ping vlan ip during reboot

        command = ['/usr/bin/ping', '-c', '10', vlan_ip]

        process = subprocess.run(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True)

        result = process.stdout

        assert result.find(f"64 bytes from {vlan_ip}") < 0, (
            f"Failed: since can ping VM external vlan IP {vlan_ip} "
            f"on vlan interface from external host during reboot")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # Get VM interface ipAddresses
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        interfaces_data = data['status']['interfaces']

        assert 1 == len(interfaces_data), (
            f"Failed: get more than one interface: {interfaces_data}"
        )

        assert "nic-1" == interfaces_data[0]['name'], (
            f"Failed: Network name did not match to added vlan: {interfaces_data}"
        )

        vlan_ip = interfaces_data[0]['ipAddress']

        # Ping vlan ip address

        command = ['/usr/bin/ping', '-c', '10', vlan_ip]

        result = subprocess.check_output(command, shell=False, encoding="utf-8")

        assert result.find(f"64 bytes from {vlan_ip}") > 0, (
            f"Failed to ping VM external vlan IP {vlan_ip} "
            f"on vlan interface from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.p0
    @pytest.mark.networks
    def test_mgmt_to_vlan_connection(self, api_client, request, client, unique_name,
                                     image_opensuse, vm_network, wait_timeout, vm_checker):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/edit-network-form-change-management-to-vlan/


        Steps:
        1. Create an external VLAN network
        2. Create a new VM
        3. Make sure that the network is set to the management network with masquerade as the type
        4. Wait until the VM boot in running state
        5. Edit VM and change management network to external VLAN with bridge type
        6. Check VM should save and reboot
        7. Check can ping the VM from an external network host
        8. Check can ssh to the VM from an external network host
        """

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        spec = api_client.vms.Spec(1, 2)
        spec.user_data += cloud_user_data.format(password=vm_credential["password"])
        vm_name = unique_name + "-mgmt-vlan"
        # Create VM
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)
        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # get data from running VM and transfer to spec
        sleep(1)  # to prevent update too fast cause code 409 conflict: 'object has been modified'
        code, data = api_client.vms.get(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        spec = spec.from_dict(data)

        # Switch to vlan network
        spec.mgmt_network = False

        spec.add_network("nic-1", f"{vm_network['namespace']}/{vm_network['name']}")

        # Update VM spec
        code, data = api_client.vms.update(vm_name, spec)
        assert 200 == code, (f"Failed to update specific vm with spec: {code}, {data}")

        code, data = api_client.vms.restart(vm_name)
        assert 204 == code, (f"Failed to restart specific vm: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # Get VM interface ipAddresses
        code, data = api_client.vms.get_status(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")

        interfaces_data = data['status']['interfaces']

        assert 1 == len(interfaces_data), (
            f"Failed: get more than one interface: {interfaces_data}"
        )

        # Determine by vlan network Name
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        ip_addresses = []

        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
            if 'interfaces' in data['status']:
                interfaces_data = data['status']['interfaces']
                ip_addresses = []
                for interface in interfaces_data:
                    # Check the ipAddress in digital format
                    if (
                        'ipAddress' in interface and
                        interface['ipAddress'].replace('.', '').isdigit()
                    ):
                        ip_addresses.append(interface['ipAddress'])

                if len(ip_addresses) > 0:
                    if 'nic-1' in interface['name']:
                        break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to get VM {vm_name} IP address, exceed given timeout\n"
                f"Still got {code} with {data}"
            )

        # Ping vlan ip address
        vlan_ip = ip_addresses[0]

        command = ['/usr/bin/ping', '-c', '50', vlan_ip]

        result = subprocess.check_output(command, shell=False, encoding="utf-8")

        assert result.find(f"64 bytes from {vlan_ip}") > 0, (
            f"Failed to ping VM external vlan IP {vlan_ip} "
            f"on vlan interface from external host")

        # SSH to vlan ip address and execute command
        _stdout, _stderr = self.ssh_client(
            client, vlan_ip, vm_credential["user"], vm_credential["password"], 'ls', wait_timeout)

        stdout = _stdout.read().decode('ascii').strip("\n")

        assert stdout.find("bin") == 0, (
            f"Failed to ssh to VM external vlan IP {vlan_ip}"
            f"on vlan interface from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.p0
    @pytest.mark.networks
    def test_vlan_to_mgmt_connection(
        self, api_client, request, client, unique_name, image_opensuse, vm_network, wait_timeout,
        host_shell, vm_shell_from_host, vm_checker
    ):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/edit-network-form-change-management-to-vlan/


        Steps:
        1. Create an external VLAN network
        2. Create a new VM
        3. Make sure that the network is set to the vlan network with bridge as the type
        4. Wait until the VM boot in running state
        5. Edit VM and change from external VLAN to management network
        6. Check VM should save and reboot
        7. Check can ping VM with management network from Harvester node
        8. Check can SSH to VM with management network from Harvester node
        9. Check can't SSH to VM with management network from external host
        """

        vip = request.config.getoption('--endpoint').strip('https://')
        vm_user, vm_passwd = vm_credential['user'], vm_credential['password']

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        spec = api_client.vms.Spec(1, 2, mgmt_network=False)
        spec.user_data += cloud_user_data.format(password=vm_passwd)
        vm_name = unique_name + "-vlan-mgmt"

        # Create VM
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)
        spec.add_network("default", f"{vm_network['namespace']}/{vm_network['name']}")

        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        # get data from running VM and transfer to spec
        code, data = api_client.vms.get(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
        spec = spec.from_dict(data)

        spec.networks = []
        spec.mgmt_network = True

        code, data = api_client.vms.update(vm_name, spec)
        assert 200 == code, (f"Failed to update specific vm with spec: {code}, {data}")

        code, data = api_client.vms.restart(vm_name)
        assert 204 == code, (f"Failed to restart specific vm: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            assert 200 == code, (f"Failed to get specific vm status: {code}, {data}")

            if 'interfaces' in data['status']:
                interfaces_data = data['status']['interfaces']
                ip_addresses = []
                if 'ipAddress' in data['status']['interfaces'][0]:

                    if 'default' in interfaces_data[0]['name']:
                        if 'domain, guest-agent' not in interfaces_data[0]['infoSource']:
                            ip_addresses.append(interfaces_data[0]['ipAddress'])
                            break
                sleep(5)
        else:
            raise AssertionError(
                f"Failed to get VM {vm_name} IP address, exceed the given timed out\n"
                f"Still got {code} with {data}"
            )

        # Check can ping management ip address from Harvester node
        mgmt_ip = ip_addresses[0]

        with host_shell.login(vip) as sh:
            stdout, stderr = sh.exec_command(f"ping -c 50 {mgmt_ip}")

        assert stdout.find(f"64 bytes from {mgmt_ip}") > 0, (
            f"Failed to ping VM management IP {mgmt_ip} "
            f"on management interface from Harvester node")

        # Check can ssh to host and execute command from Harvester node
        with vm_shell_from_host(vip, mgmt_ip, vm_user, vm_passwd) as sh:
            stdout, stderr = sh.exec_command("ls")

        assert stdout.find("bin") == 0, (
            f"Failed to ssh to VM management IP {mgmt_ip} "
            f"on management interface from Harvester node")

        # Check should not SSH to management ip address from external host
        command = ['/usr/bin/ssh', '-o', 'ConnectTimeout=5', mgmt_ip]

        with pytest.raises(subprocess.CalledProcessError) as ex:
            subprocess.check_output(command, stderr=subprocess.STDOUT,
                                    shell=False, encoding="utf-8")

        # OpenSSH returns the return code of the program that was executed on
        # the remote, unless there was an error for SSH itself, in which case
        # it returns 255
        assert ex.value.returncode == 255, ("Failed: should not be able to SSH"
                                            " to VM on management interface"
                                            f" {mgmt_ip} from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.p0
    @pytest.mark.networks
    def test_delete_vlan_from_multiple(
        self, api_client, request, client, unique_name, image_opensuse, vm_network, wait_timeout,
        host_shell, vm_checker
    ):
        """
        Manual test plan reference:
        https://harvester.github.io/tests/manual/network/delete-vlan-network-form/

        Steps:
        1. Create an external VLAN network
        2. Make sure that the network is set to the management network with masquerade as the type
        3. Add another external VLAN management
        4. Create VM
        5. Wait until the VM boot in running state
        6. Delete the external VLAN from VM
        7. Check can ping the VM on the management network
        8. Check can't SSH to VM with management network from external host
        """

        vip = request.config.getoption('--endpoint').strip('https://')

        # Check image exists
        code, data = api_client.images.get(image_opensuse.name)

        if code == 404:
            create_image_url(api_client, image_opensuse.name, image_opensuse.url, wait_timeout)

        spec = api_client.vms.Spec(1, 2)
        spec.user_data += cloud_user_data.format(password=vm_credential["password"])

        # Add network data to trigger DHCP on multiple NICs
        spec.network_data += cloud_network_data

        vm_name = unique_name + "-delete-vlan"

        # Add image
        spec.add_image(image_opensuse.name, "default/" + image_opensuse.name)

        # Add external vlan network
        spec.add_network("nic-1", f"{vm_network['namespace']}/{vm_network['name']}")

        # Create VM
        code, data = api_client.vms.create(vm_name, spec)
        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check have 2 NICs and wait until all ip address exists
        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
            if len(data['status']['interfaces']) == 2:
                if 'ipAddress' in data['status']['interfaces'][0]:
                    if 'ipAddress' in data['status']['interfaces'][1]:
                        break
                sleep(5)

        else:
            raise AssertionError(
                f"Failed to get multiple IPs on VM: {vm_name}, exceed the given timed out\n"
                f"Still got {code} with {data}"
            )

        # get data from running VM and transfer to spec
        code, data = api_client.vms.get(vm_name)
        assert 200 == code, (f"Failed to get specific vm content: {code}, {data}")
        spec = spec.from_dict(data)

        spec.networks = []
        spec.mgmt_network = True

        code, data = api_client.vms.update(vm_name, spec)
        assert 200 == code, (f"Failed to update specific vm with spec: {code}, {data}")

        code, data = api_client.vms.restart(vm_name)
        assert 204 == code, (f"Failed to restart specific vm: {code}, {data}")

        # Check VM start in running state
        check_vm_running(api_client, vm_name, wait_timeout)

        # Check until VM ip address exists
        check_vm_ip_exists(api_client, vm_name, wait_timeout)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        ip_addresses = []

        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            assert 200 == code, (f"Failed to get specific vm status: {code}, {data}")
            if 'interfaces' in data['status']:
                interfaces_data = data['status']['interfaces']
                ip_addresses = []

                interfaces = data['status']['interfaces']

                if len(interfaces) == 1 and 'ipAddress' in interfaces[0]:
                    ip_addresses.append(interfaces_data[0]['ipAddress'])

                    if 'default' in interfaces_data[0]['name']:
                        break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to get VM {vm_name} IP address, exceed the given timed out\n"
                f"Still got {code} with {data}"
            )

        # Ping management ip address
        mgmt_ip = ip_addresses[0]

        ping_command = "ping -c 50 {0}".format(mgmt_ip)

        with host_shell.login(vip) as sh:
            stdout, stderr = sh.exec_command(ping_command)

        assert stdout.find(f"64 bytes from {mgmt_ip}") > 0, (
            f"Failed to ping VM management IP {mgmt_ip} "
            f"on management interface from Harvester node: {code}, {data}")

        # #Check should not SSH to management ip address from external host
        command = ['/usr/bin/ssh', '-o', 'ConnectTimeout=5', mgmt_ip]

        with pytest.raises(subprocess.CalledProcessError) as ex:
            subprocess.check_output(command, stderr=subprocess.STDOUT,
                                    shell=False, encoding="utf-8")

        # OpenSSH returns the return code of the program that was executed on
        # the remote, unless there was an error for SSH itself, in which case
        # it returns 255
        assert ex.value.returncode == 255, ("Failed: should not be able to SSH"
                                            " to VM on management interface"
                                            f" {mgmt_ip} from external host")

        # teardown
        code, data = api_client.vms.get(vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_checker.wait_deleted(vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    def ssh_client(self, client, dest_ip, username, password, command, timeout,
                   allow_agent=False, look_for_keys=False):
        client.connect(dest_ip, username=username, password=password,
                       allow_agent=allow_agent, look_for_keys=look_for_keys,
                       timeout=timeout)

        split_command = shlex.split(command)
        _stdin, _stdout, _stderr = client.exec_command(' '.join(
            shlex.quote(part) for part in split_command), get_pty=True)
        return _stdout, _stderr

    def ssh_jumpstart(self, client, dest_ip, client_ip, client_user, client_password,
                      dest_user, dest_password, command, allow_agent=False, look_for_keys=False):
        client.connect(client_ip, username=client_user, password=client_password,
                       allow_agent=allow_agent, look_for_keys=look_for_keys)

        client_transport = client.get_transport()
        dest_addr = (dest_ip, 22)
        client_addr = (client_ip, 22)
        client_channel = client_transport.open_channel("direct-tcpip", dest_addr, client_addr)

        jumpstart = paramiko.SSHClient()
        jumpstart.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jumpstart.connect(dest_ip, username=dest_user, password=dest_password, sock=client_channel)

        split_command = shlex.split(command)
        _stdin, _stdout, _stderr = jumpstart.exec_command(' '.join(
            shlex.quote(part) for part in split_command))
        return _stdout, _stderr
