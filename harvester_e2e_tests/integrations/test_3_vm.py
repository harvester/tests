import json
import yaml
from datetime import datetime, timedelta
from time import sleep
from types import SimpleNamespace

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks",
    "harvester_e2e_tests.fixtures.settings",
    "harvester_e2e_tests.fixtures.virtualmachines",
    "harvester_e2e_tests.fixtures.volumes",
]


@pytest.fixture(scope="module")
def ubuntu_image(api_client, unique_name, image_ubuntu, image_checker):
    name = f"{image_ubuntu.name}-{unique_name}"
    code, data = api_client.images.create_by_url(name, image_ubuntu.url)
    assert 201 == code, (code, data)

    image_downloaded, (code, data) = image_checker.wait_downloaded(name)
    assert image_downloaded, (code, data)

    namespace = data['metadata']['namespace']
    assert name == data['metadata']['name'], data

    yield SimpleNamespace(
        name=name,
        id=f"{namespace}/{name}",
        ssh_user=image_ubuntu.ssh_user
    )

    # teardown
    code, data = api_client.images.delete(name, namespace)
    assert 200 == code, (code, data)
    image_deleted, (code, data) = image_checker.wait_deleted(name)
    assert image_deleted, (code, data)


@pytest.fixture(scope="class")
def available_node_names(api_client):
    status_code, nodes_info = api_client.hosts.get()
    assert status_code == 200, f"Failed to list nodes with error: {nodes_info}"

    node_names = []
    for node_info in nodes_info['data']:
        is_ready = False
        for condition in node_info.get('status', {}).get('conditions', []):
            if condition.get('type', "") == "Ready" and \
                    condition.get('status', "") == "True":
                is_ready = True
                break

        if is_ready and not node_info.get('spec', {}).get('unschedulable', False):
            node_names.append(node_info['metadata']['name'])

    assert 2 <= len(node_names), (
        f"The cluster only have {len(node_names)} available node. It's not enough."
    )
    yield node_names


@pytest.fixture(scope="class")
def cluster_network(api_client, vlan_nic):
    name = f"cnet-{vlan_nic}"
    code, data = api_client.clusternetworks.create(name)
    assert 201 == code, (code, data)
    code, data = api_client.clusternetworks.create_config(name, name, vlan_nic)
    assert 201 == code, (code, data)

    yield name

    # teardown
    code, data = api_client.clusternetworks.delete_config(name)
    assert 200 == code, (code, data)
    code, data = api_client.clusternetworks.delete(name)
    assert 200 == code, (code, data)


@pytest.fixture(scope="class")
def vm_network(api_client, unique_name, cluster_network, vlan_id, network_checker):
    name = f"vnet-{unique_name}"
    code, data = api_client.networks.create(name, vlan_id, cluster_network=cluster_network)
    assert 201 == code, (code, data)

    vnet_routed, (code, data) = network_checker.wait_vnet_routed(name)
    assert vnet_routed, (code, data)
    route = json.loads(data['metadata'].get('annotations').get('network.harvesterhci.io/route'))

    yield SimpleNamespace(
        name=name,
        vlan_id=vlan_id,
        cidr=route['cidr']
    )

    # teardown
    code, data = api_client.networks.delete(name)
    assert 200 == code, (code, data)


@pytest.fixture
def minimal_vm(api_client, unique_name, ubuntu_image, ssh_keypair, vm_checker):
    unique_vm_name = f"vm-{unique_name}"
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", ubuntu_image.id)

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    userdata['password'] = 'password'
    userdata['chpasswd'] = dict(expire=False)
    userdata['sshpwauth'] = True
    vm_spec.user_data = yaml.dump(userdata)
    code, data = api_client.vms.create(unique_vm_name, vm_spec)

    vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
    assert vm_got_ips, (
        f"Fail to start VM and get IP with error: {code}, {data}"
    )
    vm_ip = next(i['ipAddress'] for i in data['status']['interfaces'] if i['name'] == 'default')

    code, data = api_client.hosts.get(data['status']['nodeName'])
    host_ip = next(a['address'] for a in data['status']['addresses'] if a['type'] == 'InternalIP')

    yield SimpleNamespace(**{
        "name": unique_vm_name,
        "host_ip": host_ip,
        "vm_ip": vm_ip,
        "ssh_user": ubuntu_image.ssh_user
    })

    # teardown
    code, data = api_client.vms.get(unique_vm_name)
    vm_spec = api_client.vms.Spec.from_dict(data)
    vm_deleted, (code, data) = vm_checker.wait_deleted(unique_vm_name)
    assert vm_deleted, (code, data)

    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.fixture
def storage_network(api_client, cluster_network, vm_network, setting_checker):
    ''' Ref. https://docs.harvesterhci.io/v1.3/advanced/storagenetwork/#configuration-example
    '''
    yield SimpleNamespace(**{
        "vlan_id": vm_network.vlan_id,
        "cluster_network": cluster_network,
        "cidr": vm_network.cidr,
        "enable_spec": api_client.settings.StorageNetworkSpec.enable_with(
            vm_network.vlan_id, cluster_network, vm_network.cidr
        )
    })

    # teardown
    disable_spec = api_client.settings.StorageNetworkSpec.disable()
    code, data = api_client.settings.update('storage-network', disable_spec)
    assert 200 == code, (code, data)
    snet_disabled, (code, data) = setting_checker.wait_storage_net_disabled_on_harvester()
    assert snet_disabled, (code, data)
    snet_disabled, (code, data) = setting_checker.wait_storage_net_disabled_on_longhorn()
    assert snet_disabled, (code, data)


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_multiple_migrations(
    api_client, unique_name, ubuntu_image, wait_timeout, available_node_names
):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', ubuntu_image.id)
    vm_names = [f"migrate-1-{unique_name}", f"migrate-2-{unique_name}"]
    volumes = []
    for vm_name in vm_names:
        code, data = api_client.vms.create(vm_name, vm_spec)
        assert 201 == code, (
            f"Failed to create VM {vm_name} with error: {code}, {data}"
        )
        volumes.extend(api_client.vms.Spec.from_dict(data).volumes)

    vmi_data = []
    vm_name = code = data = None
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        vmi_data.clear()
        for vm_name in vm_names:
            code, data = api_client.vms.get_status(vm_name)
            if not (code == 200 and "Running" == data.get('status', {}).get('phase')):
                break
            vmi_data.append(data)
        else:
            break
        sleep(5)
    else:
        for vm_name in vm_names:
            api_client.vms.delete(vm_name)
        raise AssertionError(
            f"Can't find VM {vm_name} with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    vm_src_dst_hosts = {}  # {vm_name: [src_host, dst_host]}
    for vm_name, vm_datum in zip(vm_names, vmi_data):
        src_host = vm_datum['status']['nodeName']
        dst_host = next(n for n in available_node_names if n != src_host)
        vm_src_dst_hosts[vm_name] = [src_host, dst_host]

        code, data = api_client.vms.migrate(vm_name, dst_host)
        assert code == 204, (
            f"Can't migrate VM {vm_name} from host {src_host} to {dst_host}",
            f"Got error: {code}, {data}"
        )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        fails = []
        for vm_name, (src, dst) in vm_src_dst_hosts.items():
            code, data = api_client.vms.get_status(vm_name)
            if not data.get('status', {}).get('migrationState', {}).get('completed'):
                break
            else:
                if dst != data['status']['nodeName']:
                    fails.append(
                        f"Failed to migrate VM {vm_name} from {src} to {dst}\n"
                        f"API Status({code}): {data}"
                    )
        else:
            break
        sleep(5)
    else:
        for vm_name in vm_names:
            api_client.vms.delete(vm_name)
        raise AssertionError("\n".join(fails))

    # teardown
    for vm_name in vm_names:
        api_client.vms.delete(vm_name)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    code, data = None, None
    while endtime > datetime.now():
        fails = []
        for vm_name in vm_names:
            code, data = api_client.vms.get_status(vm_name)
            if code != 404:
                fails.append(
                    f"VM {vm_name} can't be deleted with {wait_timeout} timed out\n"
                    f"API Status({code}): {data}"
                )
                break
        else:
            break
        sleep(5)
    else:
        raise AssertionError("\n".join(fails))

    for vol in volumes:
        if vol['volume'].get('persistentVolumeClaim', {}).get('claimName'):
            api_client.volumes.delete(vol['volume']['persistentVolumeClaim']['claimName'])


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_migrate_vm_with_user_data(
    api_client, unique_name, ubuntu_image, wait_timeout, available_node_names, vm_checker
):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', ubuntu_image.id)
    vm_spec.user_data += (
        "password: test\n"
        "chpasswd:\n"
        "  expire: false\n"
        "ssh_pwauth: true\n"
    )
    code, vm_data = api_client.vms.create(unique_name, vm_spec)
    assert code == 201, (
        f"Failed to create VM {unique_name} with error: {code}, {vm_data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    data, vmi_data = None, None
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name)
        if data.get('status', {}).get('ready', False):
            code, data = api_client.vms.get_status(unique_name)
            if data['status']['conditions'][-1]['status'] == 'True':
                vmi_data = data
                break
        sleep(5)
    else:
        vm_checker.wait_deleted(unique_name)
        raise AssertionError(
            f"Can't find VM {unique_name} with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    src_host = vmi_data['status']['nodeName']
    dst_host = next(n for n in available_node_names if n != src_host)

    code, data = api_client.vms.migrate(unique_name, dst_host)
    assert code == 204, (
        f"Can't migrate VM {unique_name} from host {src_host} to {dst_host}",
        f"Got error: {code}, {data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name)
        if data.get('status', {}).get('migrationState', {}).get('completed', False):
            assert dst_host == data['status']['nodeName'], (
                f"Failed to migrate VM {unique_name} from {src_host} to {dst_host}"
            )
            break
        sleep(5)
    else:
        vm_checker.wait_deleted(unique_name)
        raise AssertionError(
            f"The migration of VM {unique_name} is not completed with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    # teardown
    vm_deleted, (code, data) = vm_checker.wait_deleted(unique_name)
    assert vm_deleted, (code, data)

    for vol in api_client.vms.Spec.from_dict(vm_data).volumes:
        if vol['volume'].get('persistentVolumeClaim', {}).get('claimName', "") != "":
            api_client.volumes.delete(vol['volume']['persistentVolumeClaim']['claimName'])


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_migrate_vm_with_multiple_volumes(
    api_client, unique_name, ubuntu_image, wait_timeout, available_node_names, vm_checker
):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', ubuntu_image.id)
    vm_spec.add_volume('disk-1', 1)
    code, vm_data = api_client.vms.create(unique_name, vm_spec)
    assert code == 201, (
        f"Failed to create VM {unique_name} with error: {code}, {vm_data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    data, vmi_data = None, None
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name)
        if data.get('status', {}).get('ready', False):
            code, data = api_client.vms.get_status(unique_name)
            if data['status']['conditions'][-1]['status'] == 'True':
                vmi_data = data
                break
        sleep(5)
    else:
        vm_checker.wait_deleted(unique_name)
        raise AssertionError(
            f"Can't find VM {unique_name} with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    src_host = vmi_data['status']['nodeName']
    dst_host = next(n for n in available_node_names if n != src_host)

    code, data = api_client.vms.migrate(unique_name, dst_host)
    assert code == 204, (
        f"Can't migrate VM {unique_name} from host {src_host} to {dst_host}",
        f"Got error: {code}, {data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name)
        if data.get('status', {}).get('migrationState', {}).get('completed', False):
            assert dst_host == data['status']['nodeName'], (
                f"Failed to migrate VM {unique_name} from {src_host} to {dst_host}"
            )
            break
        sleep(5)
    else:
        vm_checker.wait_deleted(unique_name)
        raise AssertionError(
            f"The migration of VM {unique_name} is not completed with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    # teardown
    vm_deleted, (code, data) = vm_checker.wait_deleted(unique_name)
    assert vm_deleted, (code, data)

    for vol in api_client.vms.Spec.from_dict(vm_data).volumes:
        if vol['volume'].get('persistentVolumeClaim', {}).get('claimName', "") != "":
            api_client.volumes.delete(vol['volume']['persistentVolumeClaim']['claimName'])


@pytest.mark.p0
@pytest.mark.networks
@pytest.mark.settings
@pytest.mark.virtualmachines
@pytest.mark.skip_version_if("< v1.0.3")
class TestVMWithStorageNetwork:
    def test_enable_storage_network_with_api_stopped_vm(
        self, api_client, minimal_vm, storage_network, setting_checker, vm_checker, volume_checker
    ):
        '''
        Steps:
          1. Have at least one Running VM
          2. Enable storage-network (should fail)
          3. Stop all VMs via API
          4. Enable storage-network
        '''
        code, data = api_client.settings.update('storage-network', storage_network.enable_spec)
        assert 422 == code, (
            f"storage-network should NOT be enabled with running VM: {code}, {data}"
        )

        # stop VM by API
        vm_stopped, (code, data) = vm_checker.wait_status_stopped(minimal_vm.name)
        assert vm_stopped, (code, data)

        code, data = api_client.vms.get(minimal_vm.name)
        spec = api_client.vms.Spec.from_dict(data)
        vol_names = [vol['volume']['persistentVolumeClaim']['claimName'] for vol in spec.volumes]
        vm_volumes_detached, (code, data) = volume_checker.wait_volumes_detached(vol_names)
        assert vm_volumes_detached, (code, data)

        # enable storage-network
        code, data = api_client.settings.update('storage-network', storage_network.enable_spec)
        assert 200 == code, (code, data)
        snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_harvester()
        assert snet_enabled, (code, data)
        snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_longhorn(
            storage_network.cidr
        )
        assert snet_enabled, (code, data)

    def test_enable_storage_network_with_cli_stopped_vm(
        self, api_client, ssh_keypair, minimal_vm, storage_network, setting_checker,
        vm_shell_from_host, wait_timeout, volume_checker
    ):
        ''' Refer to https://github.com/harvester/tests/issues/1022
        Steps:
          1. Have at least one Running VM
          2. Enable storage-network (should fail)
          3. Stop all VMs via VM CLI
          4. Enable storage-network
        '''
        code, data = api_client.settings.update('storage-network', storage_network.enable_spec)
        assert 422 == code, (
            f"storage-network should NOT be enabled with running VM: {code}, {data}"
        )

        # stop VM by CLI
        with vm_shell_from_host(
            minimal_vm.host_ip, minimal_vm.vm_ip, minimal_vm.ssh_user, pkey=ssh_keypair[1]
        ) as sh:
            sh.exec_command('sudo shutdown now')

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(minimal_vm.name)
            if 200 == code and "Stopped" == data.get('status', {}).get('printableStatus'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Fail to shutdown VM {minimal_vm.name} with error: {code}, {data}"
            )

        code, data = api_client.vms.get(minimal_vm.name)
        spec = api_client.vms.Spec.from_dict(data)
        vol_names = [vol['volume']['persistentVolumeClaim']['claimName'] for vol in spec.volumes]
        vm_volumes_detached, (code, data) = volume_checker.wait_volumes_detached(vol_names)
        assert vm_volumes_detached, (code, data)

        # enable storage-network
        code, data = api_client.settings.update('storage-network', storage_network.enable_spec)
        assert 200 == code, (code, data)
        snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_harvester()
        assert snet_enabled, (code, data)
        snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_longhorn(
            storage_network.cidr
        )
        assert snet_enabled, (code, data)
