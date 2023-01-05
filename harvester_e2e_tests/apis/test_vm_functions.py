# Copyright (c) 2023 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

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


def _adjusted_unique_name():
    """non-fixture unique name private function generator

    Returns:
        str: of unique name for vm
    """
    return f'vm-{(datetime.now().strftime("%m-%d-%Hh%Mm%Ss%f"))}'


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.parametrize("resource", [("cpu", 999999), ("mem", 999999), ("disk", 999999),
                                      ("mem_and_cpu", 999999), ("mem_cpu_and_disk", 999999)],
                         ids=['cpu', 'mem', 'disk', 'mem_and_cpu', 'mem_cpu_and_disk'])
def test_create_vm_no_available_resources(resource, api_client, image_id, wait_timeout):
    """Creates a VM with outlandish resources for varying elements (purposefully negative test)

    Args:
        resource (tuple): tuple of name(s) & value that can be deconstructed
        api_client (HarvesterAPI): HarvesterAPI client
        image_id (str): corresponding image_id from fixture
        wait_timeout (int): seconds for wait timeout from fixture

    Raises:
        AssertionError: when vm can not be created, all vms should be allowed to be created

    Steps:
    1. build vm object specs for outlandish resource(s) under test
    2. request to build the vm, assert that succeeds
    3. check for conditions of guest not running and vm being unschedulable

    Expected Result:
    - building vm with outlandish resource requests to be successful
    - asserting that the status condition of the vm that is built to not be running
    - asserting that the status condition of the vm that is built to be unschedulable
    """
    unique_name_for_vm = _adjusted_unique_name()
    resource_name, resource_val = resource
    overall_vm_obj = {
        'cpu': 1,
        'mem': 2,
        'disk': 10
    }

    if resource_name == 'cpu':
        overall_vm_obj['cpu'] = resource_val
    if resource_name == 'mem':
        overall_vm_obj['mem'] = resource_val
    if resource_name == 'disk':
        overall_vm_obj['disk'] = resource_val
    if resource_name == 'mem_and_cpu':
        overall_vm_obj["mem"] = resource_val
        overall_vm_obj["cpu"] = resource_val
    if resource_name == 'mem_cpu_and_disk':
        overall_vm_obj["mem"] = resource_val
        overall_vm_obj["cpu"] = resource_val
        overall_vm_obj["disk"] = resource_val

    vm = api_client.vms.Spec(overall_vm_obj['cpu'], overall_vm_obj['mem'])
    vm.add_image("disk-0", image_id, size=overall_vm_obj.get('disk'))
    code, data = api_client.vms.create(unique_name_for_vm, vm)
    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_name_for_vm)
        if 200 == code and len(data.get('status', {}).get('conditions', [])) > 1:
            check_dict = {
                'not_running': None,
                'unschedulable': None
            }
            for status_condition in data.get('status', {}).get('conditions', []):
                if status_condition.get('reason') == 'GuestNotRunning':
                    check_dict['not_running'] = True
                if status_condition.get('reason') == 'Unschedulable':
                    check_dict['unschedulable'] = True
            assert check_dict["not_running"] is True, "the vm shouldn't be running"
            assert check_dict["unschedulable"] is True, "the vm shouldn't be schedulable"
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to create VM({overall_vm_obj.get('cpu')} core, \n"
            f"{overall_vm_obj.get('mem')} RAM, \n"
            f"{overall_vm_obj.get('disk')} DISK) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.virtualmachines
def test_update_vm_machine_type(api_client, image_id, unique_vm_name, wait_timeout):
    """Create a VM with machine type of 'pc' then update to 'q35'

    Args:
        api_client (HarvesterAPI): HarvesterAPI client
        image_id (str): corresponding image_id from fixture
        wait_timeout (int): seconds for wait timeout from fixture
        unique_vm_name (str): fixture at module level based unique vm name

    Raises:
        AssertionError: failure to create, stop, update, or start

    Steps:
    1. build vm with machine type 'pc'
    2. power down vm with machine type 'pc'
    3. update vm from machine type 'pc' to machine type 'q35'
    4. power up vm

    Expected Result:
    - building a vm with machine type 'pc' to be successful
    - powering down the vm with machine type 'pc' to be successful
    - modifying the existing machine type 'pc' and updating to 'q35' to be successful
    - powering up the modified vm that now has the machine type 'q35' to be successful
    """
    cpu, mem = 1, 2

    vm = api_client.vms.Spec(cpu, mem, machine_type='pc')
    vm.add_image("disk-0", image_id)

    code, vm_create_data = api_client.vms.create(unique_vm_name, vm)

    assert 201 == code, (code, vm_create_data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 200 == code and "Running" == data.get('status', {}).get('phase'):
            code, data = api_client.vms.stop(unique_vm_name)
            assert 204 == code, "`Stop` return unexpected status code"

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
            vm_create_data['spec']['template']['spec']['domain']['machine']['type'] = 'q35'
            vm_spec = api_client.vms.Spec.from_dict(vm_create_data)
            code, data = api_client.vms.update(unique_vm_name, vm_spec)
            if 200 == code:
                code, data = api_client.vms.start(unique_vm_name)
                assert 204 == code, "`Start return unexpected status code"

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
            else:
                raise AssertionError(
                    f"Failed to Update VM({unique_vm_name}) with errors:\n"
                    f"Phase: {data.get('status', {}).get('phase')}\t"
                    f"Status: {data.get('status')}\n"
                    f"API Status({code}): {data}"
                )
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to create VM({cpu} core, {mem} RAM) with errors:\n"
            f"Phase: {data.get('status', {}).get('phase','')}\t"
            f"Status: {data.get('status', {})}\n"
            f"API Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.virtualmachines
@pytest.mark.skip(reason="TODO")
def test_vm_with_bogus_vlan(api_client, image_id, unique_vm_name, wait_timeout):
    """Test VM Creation Fails with Bogus VLAN ID

    Args:
        api_client (_type_): _description_
        image_id (_type_): _description_
        unique_vm_name (_type_): _description_
        wait_timeout (_type_): _description_

    Raises:
        AssertionError: _description_
    """
    pass


@ pytest.mark.p0
@ pytest.mark.virtualmachines
@ pytest.mark.dependency(name="minimal_vm")
def test_minimal_vm(api_client, image_id, unique_vm_name, wait_timeout):
    """
    To cover test:
    - https://harvester.github.io/tests/manual/virtual-machines/create-a-vm-with-all-the-default-values/ # noqa
    """
    cpu, mem = 1, 2
    vm = api_client.vms.Spec(cpu, mem)
    vm.add_image("disk-0", image_id)

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
            f"Phase: {data.get('status', {}).get('phase')}\t"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
