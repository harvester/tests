from time import sleep
from pathlib import Path
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images"
]


@pytest.fixture(scope="session")
def virtctl(api_client):
    code, ctx = api_client.vms.download_virtctl()

    with NamedTemporaryFile("wb") as f:
        f.write(ctx)
        f.seek(0)
        yield Path(f.name)


@pytest.fixture(scope="session")
def kubeconfig_file(api_client):
    kubeconfig = api_client.generate_kubeconfig()
    with NamedTemporaryFile("w") as f:
        f.write(kubeconfig)
        f.seek(0)
        yield Path(f.name)


@pytest.fixture(scope="module")
def image_id(api_client, opensuse_image, unique_name, wait_timeout):
    unique_image_id = f'image-{unique_name}'
    code, data = api_client.images.create_by_url(
        unique_image_id, opensuse_image.url, display_name=f"{unique_name}-{opensuse_image.name}"
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

    yield f"{data['metadata']['namespace']}/{unique_image_id}"

    code, data = api_client.images.delete(unique_image_id)


@pytest.fixture(scope="module")
def unique_vm_name(unique_name):
    return f"vm-{unique_name}"


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.dependency(name="minimal_vm")
def test_minimal_vm(api_client, image_id, unique_vm_name, wait_timeout):
    cpu, mem = 1, 2
    vm = api_client.vms.Spec(cpu, mem)
    vm.add_image("disk-0", image_id)

    code, data = api_client.vms.create(unique_vm_name, vm)

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if "Running" == data.get('status', {}).get('phase'):
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to create Minimal VM({cpu} core, {mem} RAM) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.dependency(depends=["minimal_vm"])
class TestVMOperations:
    @pytest.mark.dependency(name="pause_vm", depends=["minimal_vm"])
    def test_pause(self, api_client, unique_vm_name, wait_timeout):
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
        code, data = api_client.vms.unpause(unique_vm_name)
        assert 204 == code, "`Unpause` return unexpected status code"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            conds = data['status'].get('conditions', [])
            if 0 != len(conds) == len([c for c in conds if "Paused" not in c['type']]):
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

    @pytest.mark.dependency(depends=["stop_vm"])
    def test_start(self, api_client, unique_vm_name, wait_timeout):
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
            conds = data.get('status', {}).get('conditions', [])
            if "Running" == phase and conds and "AgentConnected" == conds[-1]['type']:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Start VM({unique_vm_name}) with errors:\n"
                f"Phase: {data.get('status', {}).get('phase')}\t"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )

    def test_restart(self, api_client, unique_vm_name, wait_timeout):
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
            if old_pods.difference(data['status'].get('activePods', old_pods)):
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
            conds = data.get('status', {}).get('conditions', [])
            if "Running" == phase and conds and "AgentConnected" == conds[-1]['type']:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Restart VM({unique_vm_name}) with errors:\n"
                f"Phase: {data.get('status', {}).get('phase')}\t"
                f"Status: {data.get('status')}\n"
                f"API Status({code}): {data}"
            )

    def test_softreboot(self, api_client, unique_vm_name, wait_timeout):
        code, data = api_client.vms.get_status(unique_vm_name)
        assert 200 == code, (
            f"unable to get VM({unique_vm_name})'s instance infos with errors:\n"
            f"Status({code}): {data}"
        )
        old_agent = data['status']['conditions'][-1]
        assert "AgentConnected" == old_agent['type'], (code, data)

        api_client.vms.softreboot(unique_vm_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(unique_vm_name)
            phase, conds = data['status']['phase'], data['status']['conditions']
            if "Running" == phase and "AgentConnected" == conds[-1]['type']:
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
        code, host_data = api_client.hosts.get()
        assert 200 == code, (code, host_data)
        code, data = api_client.vms.get_status(unique_vm_name)
        cur_host = data['status']['nodeName']

        new_host = next(h['id'] for h in host_data['data'] if cur_host != h['id'])

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
        code, host_data = api_client.hosts.get()
        assert 200 == code, (code, host_data)
        code, data = api_client.vms.get_status(unique_vm_name)
        cur_host = data['status']['nodeName']

        new_host = next(h['id'] for h in host_data['data'] if cur_host != h['id'])

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
                if 200 != code:
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
