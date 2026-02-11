import json
from time import sleep
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.hosts"
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


@pytest.fixture(scope="module")
def cpu_managers(api_client, wait_timeout):
    def wait_job_completed():
        url = "/apis/batch/v1/namespaces/harvester-system/jobs"
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            waiting = [x for x in api_client._get(url).json()['items']
                       if 'cpu-manager' in x['metadata']['name'] and x['status'].get('active')]
            if not waiting:
                break
            sleep(3)

    def wait_applied(node, status):
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.hosts.get(node)
            if 200 == code:
                label = data['metadata']['labels'].get('cpumanager')
                if status == label:
                    wait_job_completed()
                    break
            sleep(3)
        else:
            raise AssertionError(
                f"Fail to modify CPU manager on node {node} with {wait_timeout} timed out\n"
                f"The node {node} still labeling cpumanager: {label}, expected to {status}"
            )

    origin, enabled, disabled = dict(), [], []
    code, data = api_client.hosts.get()
    for node in data['data']:
        name = node['metadata']['name']
        status = json.loads(node['metadata']['labels'].get("cpumanager", 'false'))
        origin[name] = status
        if status:
            enabled.append(name)
        else:
            disabled.append(name)

    state = SimpleNamespace(
        nodes=list(origin),
        origin=origin,
        modified=list(),
        enabled=enabled,
        disabled=disabled,
        wait_applied=wait_applied,
        wait_job_completed=wait_job_completed
    )
    yield state

    # Revert the change
    code, data = api_client.hosts.get()
    for node in data['data']:
        name = node['metadata']['name']
        status = json.loads(node['metadata']['labels'].get("cpumanager", 'false'))
        if status != origin[name]:
            wait_applied(name, origin[name])


@pytest.mark.p0
@pytest.mark.hosts
@pytest.mark.smoke
class TestCPUManager:
    """ Ref: https://github.com/harvester/harvester/issues/2305 """

    @pytest.mark.dependency(name="enable_manager")
    def test_enable(self, api_client, cpu_managers, wait_timeout):
        for node in cpu_managers.nodes[::-1]:
            if not cpu_managers.origin[node]:
                code, data = api_client.hosts.cpu_manager(node, enable=True)
                assert 204 == code, (code, data)
                cpu_managers.modified.append((node, 'true'))
                break
        else:
            raise AssertionError("CPU manager has been enabled on every nodes")

        cpu_managers.wait_applied(node, 'true')

    @pytest.mark.negative
    @pytest.mark.dependency(depends=["enable_manager"])
    def test_enable_again(self, api_client, cpu_managers):
        node, modified = cpu_managers.modified[-1]
        code, data = api_client.hosts.get(node)

        assert 200 == code, (code, data)
        status = data['metadata']['labels'].get('cpumanager', 'false')
        assert status == modified, (
            f"The node {node} was modified cpumanager to {modified}, "
            f"but it's showing {status} now."
        )

        code, data = api_client.hosts.cpu_manager(node, enable=True)
        assert 400 == code and "policy is already the same" in data, (code, data)
        cpu_managers.wait_job_completed()

    @pytest.mark.dependency(name="disable_manager", depends=["enable_manager"])
    def test_disable(self, api_client, cpu_managers, wait_timeout):
        node, modified = cpu_managers.modified.pop()
        code, data = api_client.hosts.get(node)

        assert 200 == code, (code, data)
        status = data['metadata']['labels'].get('cpumanager', 'false')
        assert status == modified, (
            f"The node {node} was modified cpumanager to {modified}, "
            f"but it's showing {status} now."
        )

        code, data = api_client.hosts.cpu_manager(node, enable=False)
        assert 204 == code, (code, data)

        cpu_managers.wait_applied(node, 'false')

    @pytest.mark.negative
    def test_disable_again(self, api_client, cpu_managers):
        for node in cpu_managers.nodes[::-1]:
            if not cpu_managers.origin[node]:
                code, data = api_client.hosts.cpu_manager(node, enable=False)
                assert 400 == code and "policy is already the same" in data, (code, data)
                break
        else:
            raise AssertionError("CPU manager has been enabled on every nodes")
        cpu_managers.wait_job_completed()


@pytest.mark.p0
@pytest.mark.hosts
@pytest.mark.virtualmachines
@pytest.mark.smoke
class TestPinCPUonVM:
    """ Ref: https://github.com/harvester/harvester/issues/2305 """

    @pytest.mark.dependency(name="enable_cpu_managers")
    def test_enable_cpu_mangers(self, api_client, wait_timeout, cpu_managers):

        # scenario: 2+ nodes, all enabled, need to disable one of the node
        if len(cpu_managers.enabled) == len(cpu_managers.nodes) > 1:
            node = cpu_managers.enabled.pop()
            code, data = api_client.hosts.cpu_manager(node, enable=False)
            assert 204 == code, (code, data)
            cpu_managers.modified.append((node, True))
            cpu_managers.disabled.append(node)
            cpu_managers.wait_applied(node, 'false')

        # scenario: 3+ nodes, need to enable nodes to hit 2
        if len(cpu_managers.enabled) < 2 < len(cpu_managers.nodes):
            for _ in range(2 - len(cpu_managers.enabled)):
                node = cpu_managers.disabled.pop()
                code, data = api_client.hosts.cpu_manager(node, enable=True)
                assert 204 == code, (code, data)
                cpu_managers.modified.append((node, True))
                cpu_managers.enabled.append(node)
                cpu_managers.wait_applied(node, 'true')

        # scenario: single node
        if len(cpu_managers.disabled) == len(cpu_managers.nodes):
            node = cpu_managers.disabled.pop()
            code, data = api_client.hosts.cpu_manager(node, enable=True)
            assert 204 == code, (code, data)
            cpu_managers.modified.append((node, True))
            cpu_managers.enabled.append(node)
            cpu_managers.wait_applied(node, 'true')

    @pytest.mark.dependency(name="pin_cpu_on_vm", depends=["enable_cpu_managers"])
    def test_pin_cpu_on_vm(self, api_client, unique_name, vm_checker, ubuntu_image):
        cpu, mem, unique_vm_name = 1, 2, f"pin-cpu-{unique_name}"
        vm = api_client.vms.Spec(cpu, mem)
        vm.add_image("disk-0", ubuntu_image.id)
        vm.cpu_pinning = True

        code, data = api_client.vms.create(unique_vm_name, vm)
        assert 201 == code, (code, data)
        vm_started, (code, vmi) = vm_checker.wait_started(unique_vm_name)
        assert vm_started, (code, vmi)

        assert vmi['spec']['domain']['cpu'].get('dedicatedCpuPlacement') is True, (
            f"The VM {unique_vm_name} started but CPU not pinned."
        )

    @pytest.mark.dependency(depends=["pin_cpu_on_vm"])
    def test_reboot_vm_with_cpu_pinned(self, api_client, unique_name, vm_checker):
        unique_vm_name = f"pin-cpu-{unique_name}"

        vm_started, (code, vmi) = vm_checker.wait_restarted(unique_vm_name)
        assert vm_started, (code, vmi)
        assert vmi['spec']['domain']['cpu'].get('dedicatedCpuPlacement') is True, (
            f"The VM {unique_vm_name} started but CPU not pinned."
        )

    @pytest.mark.dependency(depends=["pin_cpu_on_vm"])
    def test_migrate_vm_with_cpu_pinned(self, api_client, unique_name, vm_checker, cpu_managers):
        assert len(cpu_managers.nodes) >= len(cpu_managers.enabled) >= 2, (
            "No enough nodes enabled cpu manager for migration"
        )
        unique_vm_name = f"pin-cpu-{unique_name}"
        code, data = api_client.vms.get_status(unique_vm_name)
        host = data['status']['nodeName']

        new_target = next(n for n in cpu_managers.enabled if n != host)
        vm_migrated, (code, data) = vm_checker.wait_migrated(unique_vm_name, new_target)
        assert vm_migrated, (
            f"Failed to Migrate VM({unique_vm_name}) from {host} to {new_target}\n"
            f"API Status({code}): {data}"
        )

    @pytest.mark.skip_if_version(
            ">= v1.7.0", "< v1.8.0", reason="https://github.com/harvester/harvester/issues/9557")
    @pytest.mark.negative
    @pytest.mark.dependency(depends=["pin_cpu_on_vm"])
    def test_disable_cpu_manager_when_vm_on_it(self, api_client, unique_name, wait_timeout):
        unique_vm_name = f"pin-cpu-{unique_name}"
        code, data = api_client.vms.get_status(unique_vm_name)
        host = data['status']['nodeName']

        code, data = api_client.hosts.cpu_manager(host, enable=False)
        assert 400 == code and "not be any running VM" in data, (code, data)

        # side-effect: teardown the VM
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
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                code, data = api_client.volumes.get(vol_name)
                if 404 == code:
                    break
                sleep(3)