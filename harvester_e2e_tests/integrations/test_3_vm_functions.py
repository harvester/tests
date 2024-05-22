from time import sleep
from datetime import datetime, timedelta
from contextlib import contextmanager

import json
import re
import pytest
import yaml
from paramiko.ssh_exception import ChannelException

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.virtualmachines"
]

# GLOBAL Vars:
MAX = 999999


@pytest.fixture(scope='module')
def bogus_vlan_net(request, api_client):
    """bogus vlan network fixture (no dhcp) on mgmt network

    Args:
        request (FixtureRequest): https://docs.pytest.org/en/7.1.x/_modules/_pytest/fixtures.html#FixtureRequest # noqa
        api_client (HarvesterAPI): HarvesterAPI client

    Yields:
        dict: created bogus network attachment definition dictionary
    """
    original_vlan_id = request.config.getoption('--vlan-id')

    existing_vm_net_code, existing_vm_net_data = api_client.networks.get()
    assert existing_vm_net_code == 200, 'we should be able to fetch vm networks from harvester'
    existing_vm_net_list = existing_vm_net_data.get('items', [])
    vlans_to_exclude = set()
    vlans_to_exclude.add(1)
    for existing_vm_net in existing_vm_net_list:
        existing_vm_net_config = existing_vm_net.get('spec', {}).get('config', '{}')
        assert existing_vm_net_config != '{}', 'existing vm net should exist'
        existing_vm_net_config_dict = json.loads(existing_vm_net_config)
        assert existing_vm_net_config_dict.get(
            'vlan', 0) != 0, 'we should be able to get the vlan off the config'
        existing_vm_net_vlan = existing_vm_net_config_dict.get('vlan')
        vlans_to_exclude.add(existing_vm_net_vlan)

    if original_vlan_id != -1:
        vlans_to_exclude.add(original_vlan_id)

    vlan_ids = set(range(2, 4095))  # 4094 is the last, 1 should always be excluded.
    code, data = api_client.networks.get()
    for net in data['items']:
        config = json.loads(net['spec'].get('config', '{}'))
        if config.get('vlan'):
            try:
                # try to remove the key, but VLAN may be used in both 'mgmt'
                # and other cluster network(s) so it might have already been removed
                vlan_ids.remove(config['vlan'])
            except KeyError:
                print(f"key, {config['vlan']} was already removed by another cluster network")

    vlan_id = vlan_ids.pop()  # Remove and return an arbitrary set element.
    vm_network_name = f'bogus-net-{vlan_id}'
    code, data = api_client.networks.create(vm_network_name, vlan_id)
    assert 201 == code, (
        f"Failed to create N.A.D. {vm_network_name} with error {code}, {data}"
    )

    yield data

    api_client.networks.delete(vm_network_name)


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


@pytest.fixture(scope="module")
def unique_vm_name(unique_name):
    return f"vm-{unique_name}"


@pytest.fixture(scope="class")
def small_volume(api_client, unique_name):
    vol_name, size = f"sv-{unique_name}", 3
    vol_spec = api_client.volumes.Spec(size)
    code, data = api_client.volumes.create(vol_name, vol_spec)

    assert 201 == code, (code, data)

    yield vol_name, size

    code, data = api_client.volumes.delete(vol_name)


@pytest.fixture(scope="class")
def stopped_vm(api_client, ssh_keypair, wait_timeout, image, unique_vm_name):
    unique_vm_name = f"stopped-{datetime.now().strftime('%m%S%f')}-{unique_vm_name}"
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])
    vm_spec.run_strategy = "Halted"

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    vm_spec.user_data = yaml.dump(userdata)

    code, data = api_client.vms.create(unique_vm_name, vm_spec)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_vm_name)
        if "Stopped" == data.get('status', {}).get('printableStatus'):
            break
        sleep(1)

    yield unique_vm_name, image['user']

    code, data = api_client.vms.get(unique_vm_name)
    vm_spec = api_client.vms.Spec.from_dict(data)

    api_client.vms.delete(unique_vm_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 404 == code:
            break
        sleep(3)

    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.fixture
def unset_cpu_memory_overcommit(api_client):
    code, data = api_client.settings.get('overcommit-config')
    assert 200 == code, (code, data)

    origin_val = json.loads(data.get('value', data['default']))
    spec = api_client.settings.Spec.from_dict(data)
    spec.cpu = spec.memory = 100
    spec.storage = origin_val['storage']
    code, data = api_client.settings.update('overcommit-config', spec)
    assert 200 == code, (code, data)

    yield json.loads(data['value']), origin_val

    spec.val = origin_val
    api_client.settings.update('overcommit-config', spec)


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.dependency(name="minimal_vm")
def test_minimal_vm(api_client, image, unique_vm_name, wait_timeout):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/virtual-machines/create-a-vm-with-all-the-default-values/ # noqa

    Steps:
        1. Create a VM with 1 CPU 2 Memory and other default values
        2. Save
    Exepected Result:
        - VM should created
        - VM should Started
    """
    cpu, mem = 1, 2
    vm = api_client.vms.Spec(cpu, mem)
    vm.add_image("disk-0", image['id'])

    code, data = api_client.vms.create(unique_vm_name, vm)

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 200 == code and "Running" == data.get('status', {}).get('phase'):
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to create Minimal VM({cpu} core, {mem} RAM) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.dependency(depends=["minimal_vm"])
class TestVMOperations:
    """
    To cover tests:
    - https://harvester.github.io/tests/manual/virtual-machines/verify-operations-like-stop-restart-pause-download-yaml-generate-template/ # noqa
    """

    @pytest.mark.dependency(name="pause_vm", depends=["minimal_vm"])
    def test_pause(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Pause the VM was created
        Exepected Result:
            - VM should change status into `Paused`
        '''
        code, data = api_client.vms.pause(unique_vm_name)
        assert 204 == code, "`Pause` return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if [c for c in data['status'].get('conditions', []) if "Paused" == c['type']]:
                conditions = data['status']['conditions']
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to pause VM({unique_vm_name}) with errors:\n"
                f"VM Status: {data['status']}\n"
                f"API Status({code}): {data}"
            )

        assert "Paused" == conditions[-1].get('type'), conditions
        assert "PausedByUser" == conditions[-1].get('reason'), conditions

    @pytest.mark.dependency(depends=["pause_vm"])
    def test_unpause(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Unpause the VM was paused
        Exepected Result:
            - VM's status should not be `Paused`
        '''
        code, data = api_client.vms.unpause(unique_vm_name)
        assert 204 == code, "`Unpause` return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            cond_types = set(c['type'] for c in data['status'].get('conditions', []))
            if {"AgentConnected"} & cond_types and not {"Paused"} & cond_types:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to unpause VM({unique_vm_name}) with errors:\n"
                f"VM Status: {data['status']}\n"
                f"API Status({code}): {data}"
            )

    @pytest.mark.dependency(name="stop_vm", depends=["minimal_vm"])
    def test_stop(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Stop the VM was created and not stopped
        Exepected Result:
            - VM's status should be changed to `Stopped`
            - VM's `RunStrategy` should be changed to `Halted`
        '''
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        code, data = api_client.vms.get(unique_vm_name)
        assert "Halted" == data['spec']['runStrategy']
        assert "Stopped" == data['status']['printableStatus']

    @pytest.mark.dependency(name="start_vm", depends=["stop_vm"])
    def test_start(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Start the VM was created and stopped
        Exepected Result:
            - VM should change status into `Running`
        '''
        code, data = api_client.vms.start(unique_vm_name)
        assert 204 == code, "`Start return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(unique_vm_name)
            strategy = data['spec']['runStrategy']
            pstats = data['status']['printableStatus']
            if "Halted" != strategy and "Running" == pstats:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            phase = data.get('status', {}).get('phase')
            conds = data.get('status', {}).get('conditions', [{}])
            if "Running" == phase and conds and "AgentConnected" == conds[-1].get('type'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )

    def test_restart(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Restart the VM was created
        Exepected Result:
            - VM's ActivePods should be updated (which means the VM restarted)
            - VM's status should update to `Running`
            - VM's qemu-agent should be connected
        '''
        code, data = api_client.vms.get_status(unique_vm_name)
        assert 200 == code, (
            f"unable to get VM({unique_vm_name})'s instance infos with errors:\n"
            f"Status({code}): {data}"
        )

        old_pods = set(data['status']['activePods'].items())

        code, data = api_client.vms.restart(unique_vm_name)
        assert 204 == code, "`Restart return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if old_pods.difference(data['status'].get('activePods', {}).items() or old_pods):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to Restart VM({unique_vm_name}), activePods is not updated.\n"
                f"Status({code}): {data}"
            )

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            phase = data.get('status', {}).get('phase')
            conds = data.get('status', {}).get('conditions', [{}])
            if "Running" == phase and conds and "AgentConnected" == conds[-1].get('type'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Restart VM({unique_vm_name}) with errors:\n"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )

    def test_softreboot(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Softreboot the VM was created
        Exepected Result:
            - VM's qemu-agent should disconnected (which means the VM rebooting)
            - VM's qemu-agent should re-connected (which means the VM boot into OS)
            - VM's status should be changed to `Running`
        '''
        code, data = api_client.vms.get_status(unique_vm_name)
        assert 200 == code, (
            f"unable to get VM({unique_vm_name})'s instance infos with errors:\n"
            f"Status({code}): {data}"
        )
        old_agent = data['status']['conditions'][-1]
        assert "AgentConnected" == old_agent['type'], (code, data)

        api_client.vms.softreboot(unique_vm_name)
        # Wait until agent disconnected (leaving OS)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if "AgentConnected" not in data['status']['conditions'][-1]['type']:
                break
            sleep(5)
        # then wait agent connected again (Entering OS)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            phase, conds = data['status']['phase'], data['status'].get('conditions', [{}])
            if "Running" == phase and "AgentConnected" == conds[-1].get('type'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Softreboot VM({unique_vm_name}) with errors:\n"
                f"API Status({code}): {data}"
            )

        old_t = datetime.strptime(old_agent['lastProbeTime'], '%Y-%m-%dT%H:%M:%SZ')
        new_t = datetime.strptime(conds[-1]['lastProbeTime'], '%Y-%m-%dT%H:%M:%SZ')

        assert new_t > old_t, (
            "Agent's probe time is not updated.\t"
            f"Before softreboot: {old_t}, After softreboot: {new_t}\n"
            f"Last API Status({code}): {data}"
        )

    def test_migrate(self, api_client, unique_vm_name, wait_timeout):
        """
        To cover test:
        - https://harvester.github.io/tests/manual/live-migration/migrate-turned-on-vm-to-another-host/ # noqa

        Steps:
            1. migrate the VM was created
        Exepected Result:
            - VM's host Node should be changed to another one
        """
        code, host_data = api_client.hosts.get()
        assert 200 == code, (code, host_data)
        code, data = api_client.vms.get_status(unique_vm_name)
        cur_host = data['status'].get('nodeName')
        assert cur_host, (
            f"VMI exists but `nodeName` is empty.\n"
            f"{data}"
        )

        new_host = next(h['id'] for h in host_data['data']
                        if cur_host != h['id'] and not h['spec'].get('taint'))

        code, data = api_client.vms.migrate(unique_vm_name, new_host)
        assert 204 == code, (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            migrating = data['metadata']['annotations'].get("harvesterhci.io/migrationState")
            if not migrating and new_host == data['status']['nodeName']:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to Migrate VM({unique_vm_name}) from {cur_host} to {new_host}\n"
                f"API Status({code}): {data}"
            )

    def test_abort_migrate(self, api_client, unique_vm_name, wait_timeout):
        """
        To cover test:
        - https://harvester.github.io/tests/manual/live-migration/abort-live-migration/

        Steps:
            1. Abort the VM was created and migrating
        Exepected Result:
            - VM should able to perform migrate
            - VM should stay in current host when migrating be aborted.
        """
        code, host_data = api_client.hosts.get()
        assert 200 == code, (code, host_data)
        code, data = api_client.vms.get_status(unique_vm_name)
        cur_host = data['status'].get('nodeName')
        assert cur_host, (
            f"VMI exists but `nodeName` is empty.\n"
            f"{data}"
        )

        new_host = next(h['id'] for h in host_data['data']
                        if cur_host != h['id'] and not h['spec'].get('taint'))

        code, data = api_client.vms.migrate(unique_vm_name, new_host)
        assert 204 == code, (code, data)

        states = ["Aborting migration", "Migrating"]
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            m_state = data['metadata']['annotations'].get("harvesterhci.io/migrationState")
            if m_state == states[-1]:
                states.pop()
                if states:
                    code, err = api_client.vms.abort_migrate(unique_vm_name)
                    assert 204 == code, (code, err)
                else:
                    break
            elif len(states) == 1 and not m_state:
                # we did abort migration, and the anootation removed
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to abort VM({unique_vm_name})'s migration, stuck on {states[-1]}\n"
                f"API Status({code}): {data}"
            )

        assert cur_host == data['status']['nodeName'], (
            f"Failed to abort VM({unique_vm_name})'s migration,"
            f"VM been moved to {data['status']['nodeName']} is not the origin host {cur_host}\n"
        )

    def test_delete(self, api_client, unique_vm_name, wait_timeout):
        '''
        Steps:
            1. Delete the VM was created
            2. Delete Volumes was belonged to the VM
        Exepected Result:
            - VM should able to be deleted and success
            - Volumes should able to be deleted and success
        '''

        code, data = api_client.vms.delete(unique_vm_name)
        assert 200 == code, (code, data)

        spec = api_client.vms.Spec.from_dict(data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Delete VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        fails, check = [], dict()
        for vol in spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            check[vol_name] = api_client.volumes.delete(vol_name)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            l_check = dict()
            for vol_name, (code, data) in check.items():
                if code not in (200, 204):
                    fails.append((vol_name, f"Failed to delete\nStatus({code}): {data}"))
                else:
                    code, data = api_client.volumes.get(vol_name)
                    if 404 != code:
                        l_check[vol_name] = (code, data)
            check = l_check
            if not check:
                break
            sleep(5)
        else:
            for vol_name, (code, data) in check.items():
                fails.append((vol_name, f"Failed to delete\nStatus({code}): {data}"))

        assert not fails, (
            f"Failed to delete VM({unique_vm_name})'s volumes with errors:\n"
            "\n".join(f"Volume({n}): {r}" for n, r in fails)
        )


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_create_stopped_vm(api_client, stopped_vm, wait_timeout):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/virtual-machines/create-a-vm-with-start-vm-on-creation-unchecked/ # noqa

    Steps:
        1. Create a VM with 1 CPU 2 Memory and runStrategy is `Halted`
        2. Save
    Exepected Result:
        - VM should created
        - VM should Stooped
        - VMI should not exist
    """
    unique_vm_name, _ = stopped_vm
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_vm_name)
        if (code == 200
                and 'Halted' == data['spec']['runStrategy']
                and 'Stopped' == data.get('status', {}).get('printableStatus')):
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Create a Stopped VM({unique_vm_name}) with errors:\n"
            f"Status({code}): {data}"
        )

    code, data = api_client.vms.get_status(unique_vm_name)
    assert 404 == code, (code, data)


@pytest.mark.p0
@pytest.mark.virtualmachines
class TestVMResource:
    @pytest.mark.parametrize("res_type", ["cpu", "memory"])
    def test_create_schedule_on_maximum(
        self, api_client, unique_vm_name, vm_checker, vm_calc, image,
        unset_cpu_memory_overcommit, res_type
    ):
        # get the node having the maximum resource
        code, data = api_client.hosts.get()
        nodes_res = [(n['metadata']['name'], vm_calc.node_resources(n)['schedulable'])
                     for n in data['data']]
        nodes_res = sorted(nodes_res, key=lambda n: n[1][res_type], reverse=True)
        expected_host, expected_res = next((cn, nd[res_type] + (cd[res_type] - nd[res_type]) / 2)
                                           for (cn, cd), (nn, nd) in zip(nodes_res, nodes_res[1:]))

        # Calculate the maximum resource
        vm_spec, namespace = api_client.vms.Spec(1, 2), 'default'
        vm_spec.add_image("disk-0", image['id'])
        data = vm_spec.to_dict(unique_vm_name, namespace)

        if res_type == 'cpu':
            exp = -2
            data['spec']['template']['spec']['domain'][res_type]['cores'] = int(expected_res) + 1
        else:
            exp = 2

        for k, resource in data['spec']['template']['spec']['domain']['resources'].items():
            resource[res_type] = vm_calc.format_unit(expected_res, max_exp=exp, suffix_space=False)

        try:
            # Create VM then verify it
            code, data = api_client.vms.create(unique_vm_name, data, namespace)
            assert 201 == code, (code, data)
            vm_started, (code, vmi) = vm_checker.wait_started(unique_vm_name)
            assert vm_started, (code, vmi)

            code, hosts = api_client.hosts.get()
            cur_res = [(n['metadata']['name'], vm_calc.node_resources(n)['schedulable'])
                       for n in hosts['data']]
            schedulables = [(name, res) for (name, res) in cur_res if res[res_type] > expected_res]
            if not schedulables:
                # General case
                assert expected_host == vmi['status']['nodeName'], (
                    f"VM started but not hosted on expected host: {expected_host}"
                )
            else:
                # ???: node's resources released while creating VM
                expected_conditions = [
                    # VM still be hosted on expected host
                    expected_host == vmi['status']['nodeName'],
                    # VM be hosted on others
                    expected_host in [name for name, _ in schedulables],
                ]
                assert any(expected_conditions), (
                    f"VM started on another host {vmi['status']['nodeName']},"
                    f" and the resource of expected host {expected_host!r} be updated."
                )
        finally:
            # We must delete the VM to release node's resources
            _ = vm_checker.wait_deleted(unique_vm_name, namespace=namespace)
            for vol in data['spec']['template']['spec']['volumes']:
                if 'persistentVolumeClaim' in vol:
                    api_client.volumes.delete(vol['persistentVolumeClaim']['claimName'])

    @pytest.mark.parametrize("res_type", ["cpu", "memory"])
    def test_update_schedule_on_maximum(
        self, api_client, vm_checker, vm_calc, stopped_vm, unset_cpu_memory_overcommit, res_type
    ):
        unique_vm_name, ssh_user = stopped_vm

        # make sure VM stopped and configure as minimal resource
        vm_stopped, (code, data) = vm_checker.wait_stopped(unique_vm_name)
        assert vm_stopped, (code, data)
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.cpu_cores, vm_spec.memory = 1, 2
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        assert 200 == code, (code, data)

        # get the node having the maximum resource
        code, data = api_client.hosts.get()
        nodes_res = [(n['metadata']['name'], vm_calc.node_resources(n)['schedulable'])
                     for n in data['data']]
        nodes_res = sorted(nodes_res, key=lambda n: n[1][res_type], reverse=True)
        expected_host, expected_res = next((cn, nd[res_type] + (cd[res_type] - nd[res_type]) / 2)
                                           for (cn, cd), (nn, nd) in zip(nodes_res, nodes_res[1:]))

        # update VM to target resource and start it
        code, data = api_client.vms.get(unique_vm_name)
        if res_type == 'cpu':
            exp = -2
            data['spec']['template']['spec']['domain'][res_type]['cores'] = int(expected_res) + 1
        else:
            exp = 2

        for k, resource in data['spec']['template']['spec']['domain']['resources'].items():
            resource[res_type] = vm_calc.format_unit(expected_res, max_exp=exp, suffix_space=False)

        try:
            code, data = api_client.vms.update(unique_vm_name, data)
            assert 200 == code, (code, data)
            vm_started, (code, vmi) = vm_checker.wait_started(unique_vm_name)
            assert vm_started, (code, vmi)

            # Verify the VM be hosted expected
            code, hosts = api_client.hosts.get()
            cur_res = [(n['metadata']['name'], vm_calc.node_resources(n)['schedulable'])
                       for n in hosts['data']]
            schedulables = [(name, res) for (name, res) in cur_res if res[res_type] > expected_res]
            if not schedulables:
                # General case
                assert expected_host == vmi['status']['nodeName'], (
                    f"VM started but not hosted on expected host: {expected_host}"
                )
            else:
                # ???: node's resources released while creating VM
                expected_conditions = [
                    # VM still be hosted on expected host
                    expected_host == vmi['status']['nodeName'],
                    # VM be hosted on others
                    expected_host in [name for name, _ in schedulables],
                ]
                assert any(expected_conditions), (
                    f"VM started on another host {vmi['status']['nodeName']},"
                    f" and the resource of expected host {expected_host!r} be updated."
                )
        finally:
            # Stop the VM
            vm_checker.wait_stopped(unique_vm_name)
            # Revert the VM to request minimal resource
            code, data = api_client.vms.get(unique_vm_name)
            vm_spec._data = data
            code, data = api_client.vms.update(unique_vm_name, vm_spec)
            assert 200 == code, (code, data)

    def test_update_cpu(
        self, api_client, ssh_keypair, vm_shell_from_host, vm_checker,
        stopped_vm
    ):
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair

        code, data = api_client.vms.start(unique_vm_name)
        assert 204 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ["default"])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Login to VM to check current CPU counts
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited, (
                f"VM {unique_vm_name} Started {vm_checker.wait_timeout} seconds"
                f", but cloud-init still in {out}"
            )

            out, err = sh.exec_command("lscpu -e=cpu | tail -1")
            out = out.strip()
        assert out.isdigit() and not err, (
            f"Failed to list cpu amount, output: {out}\nerror: {err}"
        )
        new_cpus = (int(out) + 1) + 1  # (shift to 1) + 1

        # Update CPUs
        code, data = api_client.vms.get(unique_vm_name)
        assert 200 == code, (code, data)
        spec = api_client.vms.Spec.from_dict(data)
        spec.cpu_cores = new_cpus
        code, data = api_client.vms.update(unique_vm_name, spec)
        assert 200 == code, (code, data)
        vm_restarted, ctx = vm_checker.wait_restarted(unique_vm_name)
        assert vm_restarted, (
            f"Failed to Restart VM({unique_vm_name}),"
            f" timed out while executing {ctx.callee!r}"
        )
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ["default"])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Login to VM to check updated CPUs
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
            assert cloud_inited, (
                f"VM {unique_vm_name} Started {vm_checker.wait_timeout} seconds"
                f", but cloud-init still in {out}"
            )

            out, err = sh.exec_command("lscpu -e=cpu | tail -1")
            out = out.strip()
        assert out.isdigit() and not err, (
            f"Failed to list cpu amount, output: {out}\nerror: {err}"
        )
        assert new_cpus == int(out) + 1, (
            f"Failed to update CPU to {new_cpus}, it still be {out}"
        )

        # stop the VM
        vm_checker.wait_stopped(unique_vm_name)

    def test_update_enable_usb(self, api_client, unique_vm_name, vm_checker, image):
        cpu, mem = 1, 2
        vm_spec = api_client.vms.Spec(cpu, mem)
        vm_spec.add_image("disk-0", image['id'])
        vm_spec.run_strategy = "Halted"
        vm_spec.usbtablet = False

        # Create a stopped VM without usbtablet
        code, data = api_client.vms.create(unique_vm_name, vm_spec)
        assert 201 == code, (code, data)
        with vm_checker.configure(snooze=1):
            vm_show_stopped, (code, data) = vm_checker.wait_status_stopped(unique_vm_name)
        assert vm_show_stopped, (code, data)

        # update VM to enable usbtablet and start
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.usbtablet = True
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        assert 200 == code, (code, data)
        vm_started, (code, data) = vm_checker.wait_started(unique_vm_name)
        assert vm_started, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        devices = data['spec']['domain']['devices']
        assert 'inputs' in devices
        assert 'usb' in devices['inputs'][0]['bus']
        assert 'tablet' in devices['inputs'][0]['name']
        assert 'tablet' in devices['inputs'][0]['type']

        # teardown: remove the VM
        _ = vm_checker.wait_deleted(unique_vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    def test_update_enable_user_data(self, api_client, unique_vm_name, vm_checker, image):
        cpu, mem = 1, 2
        vm_spec = api_client.vms.Spec(cpu, mem)
        vm_spec.add_image("disk-0", image['id'])
        vm_spec.run_strategy = "Halted"
        vm_spec.guest_agent = False

        # Create a stopped VM without user data (guest agent)
        code, data = api_client.vms.create(unique_vm_name, vm_spec)
        assert 201 == code, (code, data)
        with vm_checker.configure(snooze=1):
            vm_show_stopped, (code, data) = vm_checker.wait_status_stopped(unique_vm_name)
        assert vm_show_stopped, (code, data)

        # update VM to add guest agent and start
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.guest_agent = True
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        assert 200 == code, (code, data)
        vm_started, (code, data) = vm_checker.wait_started(unique_vm_name)
        assert vm_started, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        cloudinit = next(d for d in data['spec']['volumes'] if 'cloudInitNoCloud' in d)
        user_data = yaml.safe_load(cloudinit['cloudInitNoCloud']['userData'])

        assert 'packages' in user_data
        assert 'runcmd' in user_data
        assert 'qemu-guest-agent' in user_data['packages']
        assert 'systemctl' in user_data['runcmd'][0]
        assert 'enable' in user_data['runcmd'][0]
        assert '--now' in user_data['runcmd'][0]
        assert 'qemu-guest-agent.service' in user_data['runcmd'][0]

        # teardown: remove the VM
        _ = vm_checker.wait_deleted(unique_vm_name)
        for vol in vm_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)


@pytest.mark.p0
@pytest.mark.virtualmachines
class TestVMClone:
    def test_clone_running_vm(
        self, api_client, ssh_keypair, vm_checker, wait_timeout, host_shell, vm_shell, stopped_vm
    ):
        """
        To cover test:
        - (legacy) https://harvester.github.io/tests/manual/virtual-machines/clone-vm-that-is-turned-on/ # noqa
        - (new) https://github.com/harvester/tests/issues/361

        Steps:
            1. Create a VM with 1 CPU 2 Memory
            2. Start the VM and write some data
            3. Clone the VM into VM-cloned
            4. Verify VM-Cloned

        Exepected Result:
            - Cloned-VM should be available and starting
            - Cloned-VM should becomes `Running`
            - Written data should available in Cloned-VM
        """
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair
        code, data = api_client.vms.start(unique_vm_name)

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

        # Log into VM to make some data
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )
                out, err = sh.exec_command(f'echo {unique_vm_name!r} > ~/vmname')
                assert not err, (out, err)
                sh.exec_command('sync')

        # Clone VM into new VM
        cloned_name = f"cloned-{unique_vm_name}"
        code, _ = api_client.vms.clone(unique_vm_name, cloned_name)
        assert 204 == code, f"Failed to clone VM {unique_vm_name} into new VM {cloned_name}"

        # Check cloned VM is created
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(cloned_name)
            if 200 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"restored VM {cloned_name} is not created"
            )
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(cloned_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({cloned_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Log into new VM to check VM is cloned as old one
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {cloned_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command('cat ~/vmname')
            assert unique_vm_name in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )

        # Remove cloned VM and volumes
        code, data = api_client.vms.get(cloned_name)
        cloned_spec = api_client.vms.Spec.from_dict(data)
        api_client.vms.delete(cloned_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(cloned_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Delete VM({cloned_name}) with errors:\n"
                f"Status({code}): {data}"
            )
        for vol in cloned_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    def test_clone_stopped_vm(
        self, api_client, ssh_keypair, vm_checker, wait_timeout, host_shell, vm_shell, stopped_vm
    ):
        """
        To cover test:
        - (legacy) https://harvester.github.io/tests/manual/virtual-machines/clone-vm-that-is-turned-off/ # noqa
        - (new) https://github.com/harvester/tests/issues/361

        Steps:
            1. Create a VM with 1 CPU 2 Memory
            2. Start the VM and write some data
            3. Stop the VM
            4. Clone the VM into VM-cloned
            5. Verify VM-Cloned

        Exepected Result:
            - Cloned-VM should be available and stopped
            - Cloned-VM should able to start and becomes `Running`
            - Written data should available in Cloned-VM
        """
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair
        code, data = api_client.vms.start(unique_vm_name)
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

        # Log into VM to make some data
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )
                out, err = sh.exec_command(f'echo "stopped-{unique_vm_name}" > ~/vmname')
                assert not err, (out, err)
                sh.exec_command('sync')

        # Stop the VM
        code, data = api_client.vms.stop(unique_vm_name)
        assert 204 == code, "`Stop` return unexpected status code"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Stop VM({unique_vm_name}) with errors:\n"
                f"Status({code}): {data}"
            )

        # Clone VM into new VM
        cloned_name = f"cloned-{unique_vm_name}"
        code, _ = api_client.vms.clone(unique_vm_name, cloned_name)
        assert 204 == code, f"Failed to clone VM {unique_vm_name} into new VM {cloned_name}"

        # Check cloned VM is available and stooped
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(cloned_name)
            if (200 == code
               and "Halted" == data['spec'].get('runStrategy')
               and "Stopped" == data.get('status', {}).get('printableStatus')):
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Cloned VM {cloned_name} is not available and stopped"
                f"Status({code}): {data}"
            )

        # Check cloned VM started
        api_client.vms.start(cloned_name)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(cloned_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({cloned_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        # Log into new VM to check VM is cloned as old one
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {cloned_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )

                out, err = sh.exec_command('cat ~/vmname')
            assert f"stopped-{unique_vm_name}" in out, (
                f"cloud-init writefile failed\n"
                f"Executed stdout: {out}\n"
                f"Executed stderr: {err}"
            )

        # Remove cloned VM and volumes
        code, data = api_client.vms.get(cloned_name)
        cloned_spec = api_client.vms.Spec.from_dict(data)
        api_client.vms.delete(cloned_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(cloned_name)
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Delete VM({cloned_name}) with errors:\n"
                f"Status({code}): {data}"
            )
        for vol in cloned_spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)


@pytest.mark.p0
@pytest.mark.virtualmachines
class TestVMWithVolumes:
    def test_create_with_two_volumes(
        self, api_client, ssh_keypair, vm_checker, wait_timeout, host_shell, vm_shell, stopped_vm
    ):
        """
        To cover test:
        - https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-two-disk-volumes/ # noqa

        Steps:
            1. Create a VM with 1 CPU 2 Memory and 2 disk volumes
            2. Start the VM
            3. Verify the VM

        Exepected Result:
            - VM should able to start and becomes `Running`
            - 2 disk volumes should be available in the VM
            - Disk size in VM should be the same as its volume configured
        """
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.run_strategy = "RerunOnFailure"
        volumes = [('disk-1', 1), ('disk-2', 2)]
        for name, size in volumes:
            vm_spec.add_volume(name, size)

        # Start VM with 2 additional volumes
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        assert 200 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Log into VM to verify added volumes
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )
                out, err = sh.exec_command("lsblk -r")
                assert not err, (out, err)

        assert 1 + len(vm_spec.volumes) == len(re.findall('disk', out)), (
            f"Added Volumes amount is not correct.\n"
            f"lsblk output: {out}"
        )
        fails = []
        for _, size in volumes:
            if not re.search(f"vd.*{size}G 0 disk", out):
                fails.append(f"Volume size {size}G not found")

        assert not fails, (
            f"lsblk output: {out}\n"
            "\n".join(fails)
        )

        # Tear down: Stop VM and remove added volumes
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.run_strategy = "Halted"
        vol_names, vols, claims = [n for n, s in volumes], [], []
        for vd in vm_spec.volumes:
            if vd['disk']['name'] in vol_names:
                claims.append(vd['volume']['persistentVolumeClaim']['claimName'])
            else:
                vols.append(vd)
        else:
            vm_spec.volumes = vols

        api_client.vms.update(unique_vm_name, vm_spec)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(unique_vm_name)
            if (code == 200
                    and 'Halted' == data['spec']['runStrategy']
                    and 'Stopped' == data.get('status', {}).get('printableStatus')):
                break
            sleep(3)

        for vol_name in claims:
            api_client.volumes.delete(vol_name)

    def test_create_with_existing_volume(
        self, api_client, ssh_keypair, vm_checker, wait_timeout, host_shell, vm_shell, stopped_vm
    ):
        """
        To cover test:
        - https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-existing-volume/ # noqa

        Steps:
            1. Create a data volume
            2. Create a VM with 1 CPU 2 Memory and the existing data volume
            3. Start the VM
            4. Verify the VM

        Exepected Result:
            - VM should able to start and becomes `Running`
            - Disk volume should be available in the VM
            - Disk size in VM should be the same as its volume configured
        """
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair

        vol_name, size = 'disk-existing', 3
        vol_spec = api_client.volumes.Spec(size)
        code, data = api_client.volumes.create(f"{unique_vm_name}-{vol_name}", vol_spec)

        assert 201 == code, (code, data)

        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.run_strategy = "RerunOnFailure"
        vm_spec.add_existing_volume(vol_name, f"{unique_vm_name}-{vol_name}")

        # Start VM with added existing volume
        code, data = api_client.vms.update(unique_vm_name, vm_spec)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Log into VM to verify added volumes
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as sh:
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    out, err = sh.exec_command('cloud-init status')
                    if 'done' in out:
                        break
                    sleep(3)
                else:
                    raise AssertionError(
                        f"VM {unique_vm_name} Started {wait_timeout} seconds"
                        f", but cloud-init still in {out}"
                    )
                out, err = sh.exec_command("lsblk -r")
                assert not err, (out, err)

        assert 1 + len(vm_spec.volumes) == len(re.findall('disk', out)), (
            f"Added Volumes amount is not correct.\n"
            f"lsblk output: {out}"
        )

        assert f"{size}G 0 disk" in out, (
            f"existing Volume {size}G not found\n"
            f"lsblk output: {out}"
        )

        # Tear down: Stop VM and remove added volumes
        code, data = api_client.vms.get(unique_vm_name)
        vm_spec = api_client.vms.Spec.from_dict(data)
        vm_spec.run_strategy = "Halted"
        vols, claims = [], []
        for vd in vm_spec.volumes:
            if vd['disk']['name'] == vol_name:
                claims.append(vd['volume']['persistentVolumeClaim']['claimName'])
            else:
                vols.append(vd)
        else:
            vm_spec.volumes = vols

        api_client.vms.update(unique_vm_name, vm_spec)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(unique_vm_name)
            if (code == 200
                    and 'Halted' == data['spec']['runStrategy']
                    and 'Stopped' == data.get('status', {}).get('printableStatus')):
                break
            sleep(3)

        for claim in claims:
            api_client.volumes.delete(claim)


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.negative
@pytest.mark.parametrize("resource", [dict(cpu=MAX), dict(mem=MAX), dict(disk=MAX),
                                      dict(mem=MAX, cpu=MAX), dict(mem=MAX, cpu=MAX, disk=MAX)],
                         ids=['cpu', 'mem', 'disk', 'mem-and-cpu', 'mem-cpu-and-disk'])
def test_create_vm_no_available_resources(resource, api_client, image,
                                          wait_timeout, unique_vm_name, sleep_timeout):
    """Creates a VM with outlandish resources for varying elements (purposefully negative test)

    Prerequisite:
        Setting opensuse-image-url set to a valid URL for
        an opensuse image.

    Manual Test Doc(s):
        - https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-cpu-not-in-cluster/ # noqa
        - https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-memory-not-in-cluster/ # noqa
        - https://harvester.github.io/tests/manual/virtual-machines/create-vm-with-both-cpu-and-memory-not-in-cluster/ # noqa


    Args:
        request (FixtureRequest): https://docs.pytest.org/en/7.1.x/_modules/_pytest/fixtures.html#FixtureRequest # noqa
        resource (dict): dict of name(s) & value that can be deconstructed
        api_client (HarvesterAPI): HarvesterAPI client
        image (str): corresponding image from fixture
        wait_timeout (int): seconds for wait timeout from fixture
        unique_vm_name (str): string of unique vm name

    Raises:
        AssertionError: when vm can not be created, all vms should be allowed to be created

    Steps:
    1. build vm object specs for outlandish resource(s) under test
    2. request to build the vm, assert that succeeds
    3. check for conditions of guest not running and vm being unschedulable
    4. delete vm and volumes

    Expected Result:
    - building vm with outlandish resource requests to be successful
    - asserting that the status condition of the vm that is built to not be running
    - asserting that the status condition of the vm that is built to be unschedulable
    - assert deleting vm and volumes to be successful
    """
    unique_name_for_vm = f"{''.join(resource.keys())}-{unique_vm_name}"
    overall_vm_obj = dict(cpu=1, mem=2, disk=10)
    overall_vm_obj.update(resource)

    vm = api_client.vms.Spec(overall_vm_obj['cpu'], overall_vm_obj['mem'])
    vm.add_image("disk-0", image['id'], size=overall_vm_obj.get('disk'))
    code, data = api_client.vms.create(unique_name_for_vm, vm)
    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name_for_vm)
        if 200 == code and len(data.get('status', {}).get('conditions', [])) > 1:
            checks = dict(GuestNotRunning=False, Unschedulable=False)
            for condition in data['status']['conditions']:
                if condition.get('reason') in checks:
                    checks[condition['reason']] = True

            assert all(checks.values()), (
                "The VM miss condition:\n"
                " and ".join(k for k, v in checks.items() if not v)
            )
            code, data = api_client.vms.delete(unique_name_for_vm)
            assert 200 == code, (code, data)

            spec = api_client.vms.Spec.from_dict(data)
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to create VM({overall_vm_obj.get('cpu')} core, \n"
            f"{overall_vm_obj.get('mem')} RAM, \n"
            f"{overall_vm_obj.get('disk')} DISK) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name_for_vm)
        if 404 == code:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to Delete VM({unique_name_for_vm}) with errors:\n"
            f"Status({code}): {data}"
        )
    fails, check = [], dict()
    for vol in spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        check[vol_name] = api_client.volumes.delete(vol_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        l_check = dict()
        for vol_name, (code, data) in check.items():
            if code not in (200, 204):
                fails.append(
                    (vol_name, f"Failed to delete\nStatus({code}): {data}"))
            else:
                code, data = api_client.volumes.get(vol_name)
                if 404 != code:
                    l_check[vol_name] = (code, data)
        check = l_check
        if not check:
            break
        sleep(sleep_timeout)
    else:
        for vol_name, (code, data) in check.items():
            fails.append(
                (vol_name, f"Failed to delete\nStatus({code}): {data}"))
    assert not fails, (
        f"Failed to delete VM({unique_vm_name})'s volumes with errors:\n"
        "\n".join(f"Volume({n}): {r}" for n, r in fails)
    )


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.skip_version_if(
    "> v1.2.1", "> v1.3.0",
    reason="`pc type removed, ref: https://github.com/harvester/harvester/issues/5437"
)
@pytest.mark.parametrize(
    "machine_types", [("q35", "pc"), ("pc", "q35")], ids=['q35_to_pc', 'pc_to_q35']
)
def test_update_vm_machine_type(
    api_client, image, unique_vm_name, wait_timeout, machine_types, sleep_timeout
):
    """Create a VM with machine type then update to another

    Prerequisite:
        Setting opensuse-image-url set to a valid URL for
        an opensuse image.

    Manual Test Doc(s):
        - https://harvester.github.io/tests/manual/virtual-machines/create-new-vm-with-a-machine-type-pc/ # noqa
        - https://harvester.github.io/tests/manual/virtual-machines/create-new-vm-with-a-machine-type-q35/ # noqa

    Args:
        api_client (HarvesterAPI): HarvesterAPI client
        image (str): corresponding image from fixture
        wait_timeout (int): seconds for wait timeout from fixture
        unique_vm_name (str): fixture at module level based unique vm name
        machine_types (tuple)(str): deconstructed to provide starting type and desired end type

    Raises:
        AssertionError: failure to create, stop, update, or start

    Steps:
    1. build vm with starting machine type
    2. power down vm with starting machine type
    3. update vm from machine type starting to machine type ending
    4. power up vm
    5. delete vm and volumes

    Expected Result:
    - building a vm with machine type starting to be successful
    - powering down the vm with machine type starting to be successful
    - modifying the existing machine type starting and updating to ending to be successful
    - powering up the modified vm to be successful and that now has the machine type ending
    - deleting the vm to be successful
    """
    cpu, mem = 1, 2
    starting_machine_type, ending_machine_type = machine_types
    vm = api_client.vms.Spec(cpu, mem)
    vm.machine_type = starting_machine_type

    vm.add_image("disk-0", image['id'])
    unique_name_for_vm = f"{''.join(starting_machine_type)}-{unique_vm_name}"

    code, vm_create_data = api_client.vms.create(unique_name_for_vm, vm)

    assert 201 == code, (code, vm_create_data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name_for_vm)
        if 200 == code and "Running" == data.get('status', {}).get('phase'):
            code, data = api_client.vms.stop(unique_name_for_vm)
            assert 204 == code, "`Stop` return unexpected status code"
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to create VM({cpu} core, {mem} RAM) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase','')}\t"
            f"Status: {data.get('status', {})}\n"
            f"API Status({code}): {data}"
        )
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name_for_vm)
        if 404 == code:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to Stop VM({unique_name_for_vm}) with errors:\n"
            f"Status({code}): {data}"
        )
    code, data = api_client.vms.get(unique_name_for_vm)
    assert "Halted" == data['spec']['runStrategy']
    assert "Stopped" == data['status']['printableStatus']
    code, vm_to_modify = api_client.vms.get(unique_name_for_vm)
    assert code == 200
    spec = api_client.vms.Spec.from_dict(vm_to_modify)
    spec.machine_type = ending_machine_type
    code, data = api_client.vms.update(unique_name_for_vm, spec)
    result = api_client.vms.Spec.from_dict(data)
    if 200 == code and result.machine_type == ending_machine_type:
        code, data = api_client.vms.start(unique_name_for_vm)
        assert 204 == code, "`Start return unexpected status code"
    else:
        raise AssertionError(
            f"Failed to Update VM({unique_name_for_vm}) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name_for_vm)
        strategy = data['spec']['runStrategy']
        pstats = data['status']['printableStatus']
        if "Halted" != strategy and "Running" == pstats:
            code, data = api_client.vms.delete(unique_name_for_vm)
            assert 200 == code, (code, data)

            spec = api_client.vms.Spec.from_dict(data)
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to Start VM({unique_name_for_vm}) with errors:\n"
            f"Status({code}): {data}"
        )
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name_for_vm)
        if 404 == code:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to Delete VM({unique_name_for_vm}) with errors:\n"
            f"Status({code}): {data}"
        )
    fails, check = [], dict()
    for vol in spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        check[vol_name] = api_client.volumes.delete(vol_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        l_check = dict()
        for vol_name, (code, data) in check.items():
            if 200 != code:
                fails.append(
                    (vol_name, f"Failed to delete\nStatus({code}): {data}"))
            else:
                code, data = api_client.volumes.get(vol_name)
                if 404 != code:
                    l_check[vol_name] = (code, data)
        check = l_check
        if not check:
            break
    else:
        for vol_name, (code, data) in check.items():
            fails.append(
                (vol_name, f"Failed to delete\nStatus({code}): {data}"))
    assert not fails, (
        f"Failed to delete VM({unique_name_for_vm})'s volumes with errors:\n"
        "\n".join(f"Volume({n}): {r}" for n, r in fails)
    )


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.virtualmachines
def test_vm_with_bogus_vlan(api_client, image, unique_vm_name,
                            wait_timeout, bogus_vlan_net, sleep_timeout):
    """test building a VM with a VM (VLAN) Network has a bogus VLAN ID (no DHCP)

    Prerequisite:
        Setting opensuse-image-url set to a valid URL for
        an opensuse image.

    Manual Test Doc(s):
        - N/A

    Args:
        api_client (HarvesterAPI): HarvesterAPI client_
        image (str): corresponding image from fixture_
        unique_vm_name (str): fixture at module level based unique vm name
        wait_timeout (int): seconds for wait timeout from fixture
        bogus_vlan_net (dict): the data dict that contains info surrounding vm net

    Raises:
        AssertionError: fails to create, delete, or delete volumes

    Steps:
    1. build vm with a single virtio network interface
    that has a bogus vlan vm network (no dhcp)
    2. delete vm and volumes

    Expected Result:
    - assert vlan vm network can be created successfully (fixture level)
    - assert vm can be created successfully
    - assert 'ipAddresses' not in the status of running vm's interfaces
    - assert can delete vm and volumes
    """
    cpu, mem = 1, 2
    bvn = bogus_vlan_net
    vm = api_client.vms.Spec(cpu, mem)
    net_uid = f"{bvn['metadata']['namespace']}/{bvn['metadata']['name']}"
    vm = api_client.vms.Spec(cpu, mem)
    vm.add_network('no-dhcp', net_uid)
    vm.add_image("disk-0", image['id'])
    code, data = api_client.vms.create(unique_vm_name, vm)

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 200 == code and "Running" == data.get('status', {}).get('phase'):
            code, data = api_client.vms.get_status(unique_vm_name)
            assert 200 == code, (code, data)
            assert data['status']['interfaces'][1] is not None
            assert 'infoSource' in data['status']['interfaces'][1]
            assert 'mac' in data['status']['interfaces'][1]
            assert data['status']['interfaces'][1]['mac'] is not None
            assert 'name' in data['status']['interfaces'][1]
            # checking that ipAddress/es are not present due to
            # vlan that was used not having dhcp so no assignment
            # kubevirt v1 virtualmachineinstancenetworkinterface
            assert 'ipAddresses' not in data['status']['interfaces'][1]
            assert 'ipAddress' not in data['status']['interfaces'][1]
            code, data = api_client.vms.delete(unique_vm_name)
            assert 200 == code, (code, data)
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to create VM({cpu} core, {mem} RAM) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
    spec = api_client.vms.Spec.from_dict(data)

    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_vm_name)
        if 404 == code:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Failed to Delete VM({unique_vm_name}) with errors:\n"
            f"Status({code}): {data}"
        )

    fails, check = [], dict()
    for vol in spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        check[vol_name] = api_client.volumes.delete(vol_name)

    while endtime > datetime.now():
        l_check = dict()
        for vol_name, (code, data) in check.items():
            if 200 != code:
                fails.append(
                    (vol_name, f"Failed to delete\nStatus({code}): {data}"))
            else:
                code, data = api_client.volumes.get(vol_name)
                if 404 != code:
                    l_check[vol_name] = (code, data)
        check = l_check
        if not check:
            break
        sleep(sleep_timeout)
    else:
        for vol_name, (code, data) in check.items():
            fails.append(
                (vol_name, f"Failed to delete\nStatus({code}): {data}"))

    assert not fails, (
        f"Failed to delete VM({unique_vm_name})'s volumes with errors:\n"
        "\n".join(f"Volume({n}): {r}" for n, r in fails)
    )


@pytest.mark.p0
@pytest.mark.virtualmachines
class TestHotPlugVolume:
    """
    To cover test:
    - https://harvester.github.io/tests/manual/volumes/support-volume-hot-unplug/

    Steps:
        1. Create and start VM
        2. Create Data volume
        3. Attach data volume
        4. Detach data volume
    Exepected Result:
        - VM should started successfully
        - Data volume should attached and available in VM
        - Data volume should detached and unavailable in VM
        - VM should not be reboot or restart while attaching/detaching volume
    """

    disk_name = "disk-hot-plug"

    @contextmanager
    def login_to_vm_from_host(
        self, host_shell, vm_shell, wait_timeout, host_ip, ssh_user, pri_key, vm_ip
    ):
        with host_shell.login(host_ip, jumphost=True) as host_sh:
            vm_sh = vm_shell(ssh_user, pkey=pri_key)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=host_sh.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {unique_vm_name}") from login_ex

            with vm_sh as vm_sh:
                yield (vm_sh, host_sh)

    @pytest.mark.dependency(name="hot_plug_volume")
    def test_add(
        self, api_client, ssh_keypair, wait_timeout, vm_checker,
        host_shell, vm_shell, small_volume, stopped_vm
    ):
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair

        # Start VM
        code, data = api_client.vms.start(unique_vm_name)
        vm_got_ips, (code, data) = vm_checker.wait_ip_addresses(unique_vm_name, ['default'])
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        # Log into VM to verify OS is ready
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        with self.login_to_vm_from_host(
            host_shell, vm_shell, wait_timeout, host_ip, ssh_user, pri_key, vm_ip
        ) as (sh, host_sh):
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                out, err = sh.exec_command('cloud-init status')
                if 'done' in out:
                    break
                sleep(3)
            else:
                raise AssertionError(
                    f"VM {unique_vm_name} Started {wait_timeout} seconds"
                    f", but cloud-init still in {out}"
                )

        # attach volume
        vol_name, vol_size = small_volume
        code, data = api_client.vms.add_volume(unique_vm_name, self.disk_name, vol_name)

        assert 204 == code, (code, data)

        # Login to VM to verify volume hot pluged
        with self.login_to_vm_from_host(
            host_shell, vm_shell, wait_timeout, host_ip, ssh_user, pri_key, vm_ip
        ) as (sh, host_sh):
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                scsi, err = sh.exec_command(
                    "ls -d /sys/block/sd*/device/scsi_device/*"
                    " | awk -F '[/]' '{print $4,$7}'"
                )
                if scsi:
                    break
                sleep(3)
            else:
                raise AssertionError(
                    f"Hot pluged Volume {vol_name} unavailable after {wait_timeout}s\n"
                    f"STDOUT: {scsi}, STDERR: {err}"
                )

            out, err = sh.exec_command(
                f"lsblk -r | grep {scsi.split()[0]}"
            )

        assert f"{vol_size}G 0 disk" in out, (
            f"existing Volume {vol_size}G not found\n"
            f"lsblk output: {out}"
        )

    @pytest.mark.dependency(depends=["hot_plug_volume"])
    def test_remove(
        self, api_client, ssh_keypair, wait_timeout, host_shell, vm_shell, small_volume, stopped_vm
    ):
        unique_vm_name, ssh_user = stopped_vm
        pub_key, pri_key = ssh_keypair

        # remove volume
        vol_name, vol_size = small_volume
        code, data = api_client.vms.remove_volume(unique_vm_name, self.disk_name)

        assert 204 == code, (code, data)

        # Log into VM to verify volume removed
        code, data = api_client.vms.get_status(unique_vm_name)
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(data['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')

        with self.login_to_vm_from_host(
            host_shell, vm_shell, wait_timeout, host_ip, ssh_user, pri_key, vm_ip
        ) as (sh, host_sh):
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                scsi, err = sh.exec_command(
                    "ls -d1 /sys/block/* | grep 'sd'"
                )
                if not scsi:
                    break
                sleep(3)
            else:
                raise AssertionError(
                    f"Hot pluged Volume {vol_name} still available after {wait_timeout}s\n"
                    f"STDOUT: {scsi}, STDERR: {err}"
                )

            out, err = sh.exec_command(
                "lsblk -r | grep 'sd'"
            )

        assert not scsi, "SCSI device still available in `/sys/block/`"
        assert not out, "SCSI device still available in `lsblk -r`"
