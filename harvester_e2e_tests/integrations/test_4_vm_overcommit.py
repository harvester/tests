import json
from datetime import datetime, timedelta
from time import sleep

import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.virtualmachines"
]


@pytest.fixture(scope="module")
def unique_vm_name(unique_name):
    return f"vm-{unique_name}"


@pytest.fixture(scope="module")
def image(api_client, unique_name, wait_timeout, image_opensuse):
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


@pytest.fixture
def set_cpu_memory_overcommit(api_client):
    code, data = api_client.settings.get('overcommit-config')
    assert 200 == code, (code, data)

    origin_val = json.loads(data.get('value', data['default']))
    spec = api_client.settings.Spec.from_dict(data)
    spec.cpu, spec.memory = 2400, 800
    spec.storage = origin_val['storage']
    code, data = api_client.settings.update('overcommit-config', spec)
    assert 200 == code, (code, data)

    yield api_client.settings.Spec.from_dict(data), origin_val

    spec.val = origin_val
    api_client.settings.update('overcommit-config', spec)


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

    spec.value = origin_val
    api_client.settings.update('overcommit-config', spec)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.virtualmachines
class TestVMOverCommit:
    def test_create_vm_overcommit(
        self, api_client, unique_vm_name, vm_checker, vm_calc, image,
        set_cpu_memory_overcommit
    ):
        # check current resources of nodes
        code, data = api_client.hosts.get()
        nodes_res = {n['metadata']['name']: vm_calc.node_resources(n) for n in data['data']}

        occ, _ = set_cpu_memory_overcommit

        vm_spec = api_client.vms.Spec(occ.cpu // 100, occ.memory // 100)
        vm_spec.add_image("disk-0", image['id'])

        # create VM and wait it started
        code, data = api_client.vms.create(unique_vm_name, vm_spec)
        assert 201 == code, (code, data)
        try:
            vm_started, (code, vmi) = vm_checker.wait_started(unique_vm_name)
            assert vm_started, (code, vmi)

            # verify VM's limits and requests
            vmi_res = vmi['spec']['domain']['resources']
            assert int(vmi_res['limits']['cpu']) == occ.cpu // 100
            assert vmi_res['requests']['cpu'] == '1'
            assert vmi_res['limits']['memory'] == f"{occ.memory // 100}Gi"
            assert vmi_res['requests']['memory'] == '1Gi'

            # verify host's resources allocation been reduced
            code, host = api_client.hosts.get(vmi['status']['nodeName'])
            curr_res = vm_calc.node_resources(host)['schedulable']
            node_res = nodes_res[vmi['status']['nodeName']]['schedulable']
            assert 1 <= node_res['cpu'] - curr_res['cpu'] < 2
            # ???: K -> M -> G = 1000 ** 3 = 10 ** 9
            assert 10 ** 9 <= node_res['memory'] - curr_res['memory'] < 2 * 10 ** 9
        finally:
            _ = vm_checker.wait_deleted(unique_vm_name)
            for vol in data['spec']['template']['spec']['volumes']:
                if 'persistentVolumeClaim' in vol:
                    api_client.volumes.delete(vol['persistentVolumeClaim']['claimName'])

    def test_update_vm_overcommit(
        self, request, api_client, unique_vm_name, vm_checker, vm_calc, image,
        unset_cpu_memory_overcommit
    ):

        vm_spec = api_client.vms.Spec(1, 1)
        vm_spec.add_image("disk-0", image['id'])

        # create VM and wait it started
        code, data = api_client.vms.create(unique_vm_name, vm_spec)
        assert 201 == code, (code, data)
        try:
            vm_started, (code, vmi) = vm_checker.wait_started(unique_vm_name)
            assert vm_started, (code, vmi)
            vmi_res = vmi['spec']['domain']['resources']
            # when overcommit unset, limits == requests
            for k in ('cpu', 'memory'):
                assert vmi_res['limits'][k] == vmi_res['requests'][k]
            # get current node resources
            code, data = api_client.hosts.get()
            nodes_res = {n['metadata']['name']: vm_calc.node_resources(n) for n in data['data']}

            # update overcommit config and the created VM
            occ, _ = request.getfixturevalue('set_cpu_memory_overcommit')
            code, data = api_client.vms.get(unique_vm_name)
            assert 200 == code, (code, data)
            vm_spec = api_client.vms.Spec.from_dict(data)
            vm_spec.cpu_cores = occ.cpu // 100
            vm_spec.memory = occ.memory // 100

            code, data = api_client.vms.update(unique_vm_name, vm_spec)
            assert 200 == code, (code, data)
            vm_started, (code, vmi) = vm_checker.wait_restarted(unique_vm_name)
            assert vm_started, (code, vmi)
            # verify VM's limits and requests
            # code, data = api_client.vms.restart(unique_vm_name)
            # assert 204 == code, (code, data)
            # vm_restarted, (code, vmi) = vm_checker.wait_restarted(unique_vm_name)
            vmi_res = vmi['spec']['domain']['resources']
            assert int(vmi_res['limits']['cpu']) == occ.cpu // 100
            assert vmi_res['requests']['cpu'] == '1'
            assert vmi_res['limits']['memory'] == f"{occ.memory // 100}Gi"
            assert vmi_res['requests']['memory'] == '1Gi'

            # verify node's resources
            code, host = api_client.hosts.get(vmi['status']['nodeName'])
            curr_res = vm_calc.node_resources(host)['schedulable']
            node_res = nodes_res[vmi['status']['nodeName']]['schedulable']
            assert node_res['cpu'] - curr_res['cpu'] < 1
            # ???: K -> M -> G = 1000 ** 3 = 10 ** 9
            assert node_res['memory'] - curr_res['memory'] < 1 * 10 ** 9
        finally:
            _ = vm_checker.wait_deleted(unique_vm_name)
            for vol in data['spec']['template']['spec']['volumes']:
                if 'persistentVolumeClaim' in vol:
                    api_client.volumes.delete(vol['persistentVolumeClaim']['claimName'])
