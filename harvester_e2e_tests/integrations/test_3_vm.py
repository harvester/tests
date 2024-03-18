from datetime import datetime, timedelta
from time import sleep

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.fixture(scope="module")
def focal_image(api_client, unique_name, image_ubuntu, wait_timeout):
    code, data = api_client.images.create_by_url(unique_name, image_ubuntu.url)
    assert 201 == code, (
        f"Failed to upload focal image with error: {code}, {data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        if 'status' in data and 'progress' in data['status'] and \
                data['status']['progress'] == 100:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Image {unique_name} can't be ready with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield dict(ssh_user=image_ubuntu.ssh_user, id=f"{namespace}/{name}")

    is_delete = False
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        if not is_delete:
            code, data = api_client.images.delete(name, namespace)
            if code == 200:
                is_delete = True

        if is_delete:
            code, data = api_client.images.get(unique_name)
            if code == 404:
                break
        sleep(5)
    else:
        raise AssertionError(
            f"Image {unique_name} can't be deleted with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )


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


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_multiple_migrations(
    api_client, unique_name, focal_image, wait_timeout, available_node_names
):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', focal_image['id'])
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
def test_migrate_vm_with_user_data(api_client, unique_name, focal_image, wait_timeout,
                                   available_node_names):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', focal_image['id'])
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
        raise AssertionError(
            f"The migration of VM {unique_name} is not completed with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    # teardown
    api_client.vms.delete(unique_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name)
        if code == 404:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"VM {unique_name} can't be deleted with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    for vol in api_client.vms.Spec.from_dict(vm_data).volumes:
        if vol['volume'].get('persistentVolumeClaim', {}).get('claimName', "") != "":
            api_client.volumes.delete(vol['volume']['persistentVolumeClaim']['claimName'])


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_migrate_vm_with_multiple_volumes(api_client, unique_name, focal_image, wait_timeout,
                                          available_node_names):
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', focal_image['id'])
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
        raise AssertionError(
            f"The migration of VM {unique_name} is not completed with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    # teardown
    api_client.vms.delete(unique_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name)
        if code == 404:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"VM {unique_name} can't be deleted with {wait_timeout} timed out"
            f"Got error: {code}, {data}"
        )

    for vol in api_client.vms.Spec.from_dict(vm_data).volumes:
        if vol['volume'].get('persistentVolumeClaim', {}).get('claimName', "") != "":
            api_client.volumes.delete(vol['volume']['persistentVolumeClaim']['claimName'])
