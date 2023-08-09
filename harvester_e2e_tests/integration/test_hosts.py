import json
from time import sleep
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.fixture(scope="session")
def focal_image_url(request):
    base_url = request.config.getoption("--image-cache-url").strip()
    base_url = base_url or "http://cloud-images.ubuntu.com/releases/focal/release"
    return urljoin(f"{base_url}/", "ubuntu-20.04-server-cloudimg-amd64-disk-kvm.img")


@pytest.fixture(scope="module")
def focal_image(api_client, unique_name, focal_image_url, wait_timeout):
    code, data = api_client.images.create_by_url(unique_name, focal_image_url)
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

    yield dict(ssh_user="ubuntu", id=f"{namespace}/{name}")

    api_client.images.delete(name, namespace)


@pytest.fixture()
def focal_vm(api_client, focal_image, wait_timeout):
    unique_name = f'vm-{datetime.now().strftime("%Hh%Mm%Ss%f-%m-%d")}'
    vm_spec = api_client.vms.Spec(1, 1)
    vm_spec.add_image('disk-0', focal_image['id'])
    code, data = api_client.vms.create(unique_name, vm_spec)
    assert 201 == code, (
        f"Failed to create VM {unique_name} with error: {code}, {data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_name)
        if data.get('status', {}).get('ready', False):
            code, data = api_client.vms.get_status(unique_name)
            if data['status']['conditions'][-1]['status'] == 'True':
                break
        sleep(5)
    else:
        raise AssertionError(
            f"Can't find VM {unique_name} with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    data['name'] = data['metadata']['name']
    data['namespace'] = data['metadata']['namespace']
    yield data

    code, data = api_client.vms.get(unique_name)
    if 200 == code:  # ???: https://github.com/harvester/harvester/issues/4388
        volume_name = ""
        for volume in data['spec']['template']['spec']['volumes']:
            if volume['name'] == 'disk-0':
                volume_name = volume['persistentVolumeClaim']['claimName']
        api_client.vms.delete(unique_name)
        api_client.volumes.delete(volume_name)


@pytest.fixture(scope="class")
def available_node_names(api_client):
    status_code, nodes_info = api_client.hosts.get()
    assert status_code == 200, f"Failed to list nodes with error: {nodes_info}"

    node_names = []
    for node_info in nodes_info.get('data', []):
        is_ready = False
        for condition in node_info.get('status', {}).get('conditions', []):
            if condition.get('type', "") == "Ready" and \
                    condition.get('status', "") == "True":
                is_ready = True
                break

        if is_ready and not node_info.get('spec', {}).get('unschedulable', False):
            node_names.append(node_info['metadata']['name'])

    return node_names


@pytest.fixture(scope="class")
def vm_force_reset_policy(api_client):
    # update vm-force-reset-policy to 10s, so we don't need to wait 300s to force remove VM
    code, data = api_client.settings.get("vm-force-reset-policy")
    assert 200 == code, (
        f"Failed to get vm-force-reset-policy setting with error: {code}, {data}")
    original_value = data.get("value", data['default'])

    spec = dict(enable=True, period=10)
    code, data = api_client.settings.update("vm-force-reset-policy", dict(value=json.dumps(spec)))
    assert 200 == code, (
        f"Failed to update vm-force-reset-policy setting with error: {code}, {data}"
    )

    yield spec

    # teardown
    updates = {"value": original_value}
    api_client.settings.update("vm-force-reset-policy", updates)


@pytest.mark.hosts
@pytest.mark.p1
@pytest.mark.host_management
class TestHostState:
    @pytest.mark.dependency(name="host_poweroff")
    def test_poweroff_state(self, api_client, host_state, wait_timeout, available_node_names):
        """
        Test the hosts are the nodes which make the cluster
        Covers:
            hosts-01-Negative test-Verify the state for Powered down node
        """
        assert 2 <= len(available_node_names), (
            f"The cluster only have {len(available_node_names)} available node."
            " It's not enough for power off test."
        )
        _, node = api_client.hosts.get(available_node_names[-1])

        node_ip = next(val["address"] for val in node['status']['addresses']
                       if val["type"] == "InternalIP")

        rc, out, err = host_state.power(node['id'], node_ip, on=False)
        assert rc == 0, (f"Failed to PowerOff node {node['id']} with error({rc}):\n"
                         f"stdout: {out}\n\nstderr: {err}")
        sleep(host_state.delay)  # Wait for the node to disappear
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, metric = api_client.hosts.get_metrics(node['id'])
            if 404 == code:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Node {node['id']} still available after PowerOff script executed"
                f", script path: {host_state.path}"
            )

        _, node = api_client.hosts.get(node['id'])
        assert node["metadata"]["state"]["name"] in ("in-progress", "unavailable")

    @pytest.mark.dependency(name="host_poweron", depends=["host_poweroff"])
    def test_poweron_state(self, api_client, host_state, wait_timeout, available_node_names):
        assert 2 <= len(available_node_names), (
            f"The cluster only have {len(available_node_names)} available node."
            " It's not enough for power on test."
        )
        _, node = api_client.hosts.get(available_node_names[-1])

        assert node['metadata']['state']['error'], (
            f"The node {available_node_names[-1]} was not poweroff.\n"
            f"Node Status: {node['metadata']['status']}"
        )

        node_ip = next(val["address"] for val in node['status']['addresses']
                       if val["type"] == "InternalIP")

        rc, out, err = host_state.power(node['id'], node_ip, on=True)
        assert rc == 0, (f"Failed to PowerOn node {node['id']} with error({rc}):\n"
                         f"stdout: {out}\n\nstderr: {err}")
        sleep(host_state.delay)  # Wait for the node to appear
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            _, metric = api_client.hosts.get_metrics(node['id'])
            state = metric.get("metadata", {}).get("state", {})
            if state and not state.get("error") and state.get('name') != 'unavailable':
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Node {node['id']} still unavailable after PowerOn script executed"
                f", script path: {host_state.path}"
            )

        _, node = api_client.hosts.get(node['id'])
        assert "active" == node["metadata"]["state"]["name"]


@pytest.mark.hosts
@pytest.mark.p0
def test_verify_host_info(api_client):
    status_code, nodes_info = api_client.hosts.get()

    assert 200 == status_code, f"Failed to list nodes with error: {nodes_info}"

    fails = []
    for node in nodes_info['data']:
        node_name = node.get('metadata', {}).get('name', "")
        if node_name == "":
            fails.append((node['id'], "node name can't be empty"))

        cpus = node.get('status', {}).get('capacity', {}).get('cpu', 0)
        if cpus == 0:
            fails.append((node['id'], "cpu should not be zero"))

        mems = node.get('status', {}).get('capacity', {}).get('memory', "0Ki")
        mems = "".join(c for c in mems if c.isdigit())
        mems = mems or "0"
        if int(mems, 10) == 0:
            fails.append((node['id'], "memory should not be zero"))

    assert not fails, (
        "Failed to get node information with errors:\n",
        "\n".join(f"Node {n}: {r}" for n, r in fails)
    )


@pytest.mark.hosts
@pytest.mark.p0
def test_maintenance_mode_trigger_vm_migrate(
    api_client, focal_vm, wait_timeout, available_node_names
):
    assert 2 <= len(available_node_names), (
        f"The cluster only have {len(available_node_names)} available node. \
            It's not enough for migration test."
    )

    code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
    assert 200 == code, (
        f"Can't get VMI {focal_vm['namespace']}/{focal_vm['name']} with error: {code}, {data}"
    )
    src_host = data['status']['nodeName']

    code, data = api_client.hosts.maintenance_mode(src_host, enable=True)
    assert 204 == code, (
        f"Failed to enable maintenance mode on node {src_host} with error: {code}, {data}",
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.hosts.get(src_host)
        if data.get('metadata', {}) \
                .get('annotations', {}) \
                .get('harvesterhci.io/maintain-status', '') == "completed":
            break
        sleep(5)
    else:
        raise AssertionError(
            f"The maintain-status of node {src_host} can't be completed \
                with {wait_timeout} timed out\n"
            f"Got error: {code}, {data}"
        )

    code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
    assert 200 == code, (
        f"Failed to get VM {focal_vm['namespace']}/{focal_vm['name']} with error: {code}, {data}"
    )
    assert src_host != data['status']['nodeName'], (
        f"Failed to migrate VM {focal_vm['namespace']}/{focal_vm['name']} \
            from {src_host} to another node"
    )
    assert 'Running' == data['status']['phase'], (
        f"Failed to migrate VM {focal_vm['namespace']}/{focal_vm['name']}, \
            it's not running after migration"
    )

    # teardown
    code, data = api_client.hosts.maintenance_mode(src_host, enable=False)
    assert 204 == code, (
        f"Failed to disable maintenance mode on node {src_host} with error: {code}, {data}",
    )


@pytest.mark.hosts
@pytest.mark.p0
@pytest.mark.dependency(depends=["host_poweroff", "host_poweron"])
def test_poweroff_node_trigger_vm_reschedule(
    api_client, host_state, focal_vm, wait_timeout, available_node_names, vm_force_reset_policy
):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/hosts/vm_rescheduled_after_host_poweroff

    Prerequisite:
        - Cluster's nodes >= 2
    Steps:
        1. Create a VM with 1 CPU 1 Memory and runStrategy is `RerunOnFailure`
        2. Power off the node hosting the VM
        3. Verify the VM
    Exepected Result:
        - VM should created and started successfully
        - Node should be unavailable after shutdown
        - VM should restarted automatically
    """
    assert 2 <= len(available_node_names), (
        f"The cluster only have {len(available_node_names)} available node. \
            It's not enough for migration test."
    )

    code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
    assert 200 == code, (
        f"Can't get VMI {focal_vm['namespace']}/{focal_vm['name']} with error: {code}, {data}"
    )
    old_uid = data['metadata']['uid']

    # poweroff host
    _, node = api_client.hosts.get(data['status']['nodeName'])
    node_ip = next(val["address"] for val in node['status']['addresses']
                   if val["type"] == "InternalIP")
    rc, out, err = host_state.power(node['id'], node_ip, on=False)
    assert rc == 0, (f"Failed to PowerOff node {node['id']} with error({rc}):\n"
                     f"stdout: {out}\n\nstderr: {err}")
    sleep(host_state.delay)  # Wait for the node to disappear
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, metric = api_client.hosts.get_metrics(node['id'])
        if 404 == code:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Node {node['id']} still available after PowerOff script executed"
            f", script path: {host_state.path}"
        )

    try:
        # XXX: default `node-monitor-grace-period` is 5 minutes
        # ref: https://github.com/harvester/harvester/issues/3896#issuecomment-1553154738
        sleep(5 * 60 + vm_force_reset_policy['period'])
        # check vm is restarted
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
            if old_uid != data['metadata']['uid'] and "Running" == data['status'].get('phase'):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"VM {focal_vm['namespace']}/{focal_vm['name']} can't be Running \
                    with {wait_timeout} timed out\n"
                f"Got error: {code}, {data}"
            )
    finally:
        # teardown
        rc, out, err = host_state.power(node['id'], node_ip, on=True)
        assert rc == 0, (f"Failed to PowerOn node {node['id']} with error({rc}):\n"
                         f"stdout: {out}\n\nstderr: {err}")
        sleep(host_state.delay)  # Wait for the node to appear
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            _, metric = api_client.hosts.get_metrics(node['id'])
            if not metric.get("metadata", {}).get("state", {}).get("error"):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Node {node['id']} still unavailable after PowerOn script executed"
                f", script path: {host_state.path}"
            )


@pytest.mark.p0
@pytest.mark.hosts
@pytest.mark.dependency(depends=["host_poweroff", "host_poweron"])
def test_delete_vm_after_host_shutdown(
    api_client, host_state, wait_timeout, focal_vm, available_node_names
):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/hosts/delete_vm_after_host_shutdown

    Prerequisite:
        - Cluster's nodes >= 2
    Steps:
        1. Create a VM with 1 CPU 1 Memory and runStrategy is `RerunOnFailure`
        2. Power off the node hosting the VM
        3. Delete the VM
        4. Verify the VM
    Exepected Result:
        - VM should created and started successfully
        - Node should be unavailable after shutdown
        - VM should able to be deleted
    """
    assert 2 <= len(available_node_names), (
        f"The cluster only have {len(available_node_names)} available node."
        " It's not enough for test."
    )

    code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
    assert 200 == code, (
        f"Can't get VMI {focal_vm['namespace']}/{focal_vm['name']} with error: {code}, {data}"
    )

    # poweroff host
    _, node = api_client.hosts.get(data['status']['nodeName'])
    node_ip = next(val["address"] for val in node['status']['addresses']
                   if val["type"] == "InternalIP")
    rc, out, err = host_state.power(node['id'], node_ip, on=False)
    assert rc == 0, (f"Failed to PowerOff node {node['id']} with error({rc}):\n"
                     f"stdout: {out}\n\nstderr: {err}")
    sleep(host_state.delay)  # Wait for the node to disappear
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, metric = api_client.hosts.get_metrics(node['id'])
        if 404 == code:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Node {node['id']} still available after PowerOff script executed"
            f", script path: {host_state.path}"
        )

    try:
        # Delete VM and check it been deleted
        code, data = api_client.vms.delete(focal_vm['name'], focal_vm['namespace'])
        assert 200 == code, (code, data)
        spec = api_client.vms.Spec.from_dict(data)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(focal_vm['name'], focal_vm['namespace'])
            if 404 == code:
                break
            sleep(3)
        else:
            raise AssertionError(
                f"Failed to Delete VM({focal_vm['name']}) with errors:\n"
                f"Status({code}): {data}"
            )

        fails, check = [], dict()
        for vol in spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            code, data = api_client.volumes.delete(vol_name)
            if 200 == code:
                check[vol_name] = (code, data)
            else:
                fails[vol_name] = (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            for vol_name, (code, data) in check.copy().items():
                code, data = api_client.volumes.get(vol_name)
                if 404 == code:
                    check.pop(vol_name)
            if not check:
                break
            sleep(5)
        else:
            for vol_name, (code, data) in check.items():
                fails.append((vol_name, f"Failed to delete\nStatus({code}): {data}"))

        assert not fails, (
            f"Failed to delete VM({focal_vm['name']})'s volumes with errors:\n"
            "\n".join(f"Volume({n}): {r}" for n, r in fails)
        )
    finally:
        # teardown: power on the host
        rc, out, err = host_state.power(node['id'], node_ip, on=True)
        assert rc == 0, (f"Failed to PowerOn node {node['id']} with error({rc}):\n"
                         f"stdout: {out}\n\nstderr: {err}")
        sleep(host_state.delay)  # Wait for the node to disappear
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            _, metric = api_client.hosts.get_metrics(node['id'])
            if not metric.get("metadata", {}).get("state", {}).get("error"):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Node {node['id']} still unavailable after PowerOn script executed"
                f", script path: {host_state.path}"
            )


@pytest.mark.p0
@pytest.mark.hosts
@pytest.mark.dependency(depends=["host_poweroff", "host_poweron"])
def test_vm_restarted_after_host_reboot(
    api_client, host_state, wait_timeout, focal_vm, available_node_names
):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/hosts/vm_migrated_after_host_reboot

    Prerequisite:
        - Cluster's nodes >= 2
    Steps:
        1. Create a VM with 1 CPU 1 Memory and runStrategy is `RerunOnFailure`
        2. Reboot the node hosting the VM
        4. Verify the VM
    Exepected Result:
        - VM should created
        - Node should be unavailable while rebooting
        - VM should be restarted
    """
    assert 2 <= len(available_node_names), (
        f"The cluster only have {len(available_node_names)} available node. \
            It's not enough for migration test."
    )

    code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
    assert 200 == code, (
        f"Can't get VMI {focal_vm['namespace']}/{focal_vm['name']} with error: {code}, {data}"
    )
    old_uid = data['metadata']['uid']

    # reboot the host
    _, node = api_client.hosts.get(data['status']['nodeName'])
    node_ip = next(val["address"] for val in node['status']['addresses']
                   if val["type"] == "InternalIP")
    rc, out, err = host_state.reboot(node['id'], node_ip)
    assert rc == 0, (f"Failed to reboot node {node['id']} with error({rc}):\n"
                     f"stdout: {out}\n\nstderr: {err}")

    endtime = datetime.now() + timedelta(seconds=wait_timeout + host_state.delay)
    while endtime > datetime.now():
        code, metric = api_client.hosts.get_metrics(node['id'])
        if 404 == code:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Node {node['id']} still available after reboot script executed"
            f", script path: {host_state.path}"
        )

    # check vm is restarted
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(focal_vm['name'], focal_vm['namespace'])
        if (200 == code and old_uid != data['metadata']['uid']
                and "Running" == data['status'].get('phase')):
            break
        sleep(5)
    else:
        raise AssertionError(
            "VMI didn't changed after host rebooted.\n"
            f"Got error: {code}, {data}"
        )

    # check the node is back
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        _, metric = api_client.hosts.get_metrics(node['id'])
        if not metric.get("metadata", {}).get("state", {}).get("error"):
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Node {node['id']} still unavailable after reboot script executed"
            f", script path: {host_state.path}"
        )
