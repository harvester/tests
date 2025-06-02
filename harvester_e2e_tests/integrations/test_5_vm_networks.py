import re
import yaml
import json
from time import sleep
from datetime import datetime, timedelta
from operator import add
from functools import reduce
from ipaddress import ip_address, ip_network

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks",
    "harvester_e2e_tests.fixtures.virtualmachines"
]


@pytest.fixture(scope="session")
def gen_ifconfig():
    # eth/eno/ens(idx) | enp(idx)s[0-9]
    pattern = r"(?:(e(?:th|no|ns))(\d+)|(enp)(\d+)(s\d+))"

    def replace_to(idx):
        def _repl(match):
            p1, idx1, p2, idx2, tail = match.groups()
            return f"{p1}{int(idx1)+idx}" if not tail else f"{p2}{int(idx2)+idx}{tail}"
        return _repl

    def generate_ifconfig(ifname, idx=0):
        return {
            "type": "physical",
            "name": re.sub(pattern, replace_to(idx), ifname),
            "subnets": [dict(type="dhcp")]
        }

    return generate_ifconfig


@pytest.fixture(scope="module")
def image(api_client, image_opensuse, unique_name, wait_timeout):
    unique_image_id = f'image-{unique_name}'
    code, data = api_client.images.create_by_url(
        unique_image_id, image_opensuse.url, display_name=f"{unique_name}-{image_opensuse.name}"
    )

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_image_id)
        if 100 == data.get('status', {}).get('progress', 0):
            break
        sleep(3)
    else:
        raise AssertionError(
            "Failed to create Image with error:\n"
            f"Status({code}): {data}"
        )

    yield dict(id=f"{data['metadata']['namespace']}/{unique_image_id}",
               user=image_opensuse.ssh_user)

    code, data = api_client.images.delete(unique_image_id)


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


@pytest.fixture(scope="class")
def minimal_vm(api_client, ssh_keypair, wait_timeout, unique_name, vm_checker, image):
    unique_vm_name = f"{datetime.now().strftime('%m%S%f')}-{unique_name}"
    cpu, mem = 1, 2
    pub_key, _ = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    vm_spec.user_data = yaml.dump(userdata)

    code, data = api_client.vms.create(unique_vm_name, vm_spec)
    assert 201 == code, (code, data)
    vm_started, (code, data) = vm_checker.wait_interfaces(unique_vm_name)

    yield unique_vm_name, image['user']

    code, data = api_client.vms.get(unique_vm_name)
    vm_spec = api_client.vms.Spec.from_dict(data)
    vm_deleted, (code, data) = vm_checker.wait_deleted(unique_vm_name)
    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.fixture(scope="class")
def two_mirror_vms(api_client, ssh_keypair, unique_name, vm_checker, image, vm_network):
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])
    vm_spec.mgmt_network = False
    vm_spec.add_network('nic-1', f"{vm_network['namespace']}/{vm_network['name']}")

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    vm_spec.user_data = yaml.dump(userdata)
    vm_names = [f"vm{idx}-{unique_name}" for idx in range(1, 3)]

    for vm_name in vm_names:
        code, data = api_client.vms.create(vm_name, vm_spec)
        assert 201 == code, (code, data)

    yield vm_names, image['user']

    params = dict(removedDisks="disk-0", propagationPolicy="Foreground")
    for vm_name in vm_names:
        vm_checker.wait_deleted(vm_name, params=params)


@pytest.mark.p0
@pytest.mark.networks
@pytest.mark.virtualmachines
class TestVMNetwork:
    @pytest.mark.sanity
    @pytest.mark.dependency(name="add_vlan")
    def test_add_vlan(
        self, api_client, ssh_keypair, vm_mgmt_static, vm_checker, vm_shell_from_host, vm_network,
        minimal_vm, gen_ifconfig
    ):
        # clean cloud-init for rerun, and get the correct ifname
        (unique_vm_name, ssh_user), (_, pri_key) = minimal_vm, ssh_keypair
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited, (out, err)
            out, err = sh.exec_command("sudo cloud-init clean")
            out, err = sh.exec_command("sudo cloud-init status")
            assert "not run" in out, (out, err)
            out, err = sh.exec_command("ip --json a s")
            assert not err
        ifname = next(i['ifname'] for i in json.loads(out) if i['link_type'] != 'loopback')
        # https://cloudinit.readthedocs.io/en/22.4.2/topics/network-config-format-v1.html#subnet-ip
        # and https://harvesterhci.io/kb/multiple-nics-vm-connectivity/#cloud-init-config
        nic_config = [gen_ifconfig(ifname, idx=i) for i in range(2)]
        nic_config[0]['subnets'] = [vm_mgmt_static]

        # add vlan NIC and network data then restart VM
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.add_network('nic-1', f"{vm_network['namespace']}/{vm_network['name']}")
        vm_spec.network_data = "#cloud-config\n" + yaml.dump({
            "version": 1,
            "config": nic_config
        })
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        assert 200 == code, (code, data)
        vm_restarted, ctx = vm_checker.wait_restarted(unique_vm_name)
        assert vm_restarted, (
            f"Failed to Restart VM({unique_vm_name}),"
            f" timed out while executing {ctx.callee!r}"
        )
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited and not err, (out, err)
            out, err = sh.exec_command("ip --json -4 a s")
        ips = [j['local'] for i in json.loads(out) for j in i['addr_info']]
        vlan_ip_range = ip_network(vm_network['cidr'])

        def get_vlan_ip(ctx):
            if ctx.callee == 'vm.get_status':
                return all(iface.get('ipAddress') for iface in ctx.data['status']['interfaces']
                           if iface['name'] != 'default')
            return True
        # ???: status data from API will have delay a bit
        vm_got_ips, (code, data) = vm_checker.wait_interfaces(unique_vm_name, callback=get_vlan_ip)
        assert vm_got_ips, (code, data)
        vm_vlan_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                          if iface['name'] != 'default')
        assert ip_address(vm_vlan_ip) in vlan_ip_range and vm_vlan_ip in ips

    @pytest.mark.smoke
    @pytest.mark.dependency(depends=["add_vlan"])
    def test_ssh_connection(
        self, api_client, ssh_keypair, vm_checker, vm_network, minimal_vm
    ):
        (unique_vm_name, ssh_user), (_, pri_key) = minimal_vm, ssh_keypair
        vm_started, (code, data) = vm_checker.wait_interfaces(unique_vm_name)
        assert vm_started, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] != 'default')
        try:
            with vm_checker.wait_ssh_connected(vm_ip, ssh_user, pkey=pri_key) as sh:
                out, err = sh.exec_command("ip -brief a s")
                assert vm_ip in out and not err
        except AssertionError as ex:
            raise ex
        except Exception as ex:
            raise AssertionError(
                f"Unable to login to VM via VLAN IP {vm_ip}"
            ) from ex

    @pytest.mark.sanity
    def test_vms_on_same_vlan(
        self, api_client, ssh_keypair, vm_checker, vm_network, two_mirror_vms
    ):
        _, pri_key = ssh_keypair
        vm_names, ssh_user = two_mirror_vms

        def get_vlan_ip(ctx):
            if ctx.callee == 'vm.get_status':
                return all(iface.get('ipAddress') for iface in ctx.data['status']['interfaces']
                           if iface['name'] != 'default')
            return True
        # Verify VM having IP which belongs to VLAN
        vm_info, vlan_ip_range = [], ip_network(vm_network['cidr'])
        for vm_name in vm_names:
            vm_got_ips, (code, data) = vm_checker.wait_interfaces(vm_name, callback=get_vlan_ip)
            assert vm_got_ips, (
                f"Failed to Start VM({vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )
            vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                         if iface['name'] != 'default')
            assert ip_address(vm_ip) in vlan_ip_range
            vm_info.append((vm_name, vm_ip))

        # verify Ping from each
        for (src_name, src_ip), (dst_name, dst_ip) in zip(vm_info, vm_info[::-1]):
            try:
                with vm_checker.wait_ssh_connected(src_ip, ssh_user, pkey=pri_key) as sh:
                    out, err = sh.exec_command(f"ping -c5 {dst_ip}")
                    assert '100% packet loss' not in out, (
                        f"Failed to ping VM({dst_name!r}, {dst_ip}) <- VM({src_name!r}, {src_ip})"
                    )
            except AssertionError as ex:
                raise ex
            except Exception as ex:
                raise AssertionError(
                    f"Unable to login to VM via VLAN IP {src_ip}"
                ) from ex
