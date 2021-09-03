# Copyright (c) 2021 SUSE LLC
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

from harvester_e2e_tests import utils
import pytest
import time
import polling2

pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair'
]


@pytest.fixture(scope='function')
def windows_vm(request, admin_session, windows_image, keypair,
               harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, windows_image,
                              harvester_api_endpoints, keypair=keypair)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_vm(request, admin_session, harvester_api_endpoints,
                        vm_json)


@pytest.fixture(scope='function')
def single_vm(request, admin_session, image, keypair, harvester_api_endpoints):
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints, keypair=keypair)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_vm(request, admin_session, harvester_api_endpoints,
                        vm_json)


# NOTE: we could have used the 'class' scope and use the code similar to
# above so we have multiple VMs running till class teardown. But we want to
# keep the tests clean so we are explicitly creating multiple VMs for a
# single test.
@pytest.fixture(scope='function')
def multiple_vms(request, admin_session, ubuntu_image, k3os_image,
                 opensuse_image, windows_image, keypair,
                 harvester_api_endpoints):
    vms = []
    vms.append(utils.create_vm(request, admin_session, ubuntu_image,
                               harvester_api_endpoints, keypair=keypair))
    vms.append(utils.create_vm(request, admin_session, k3os_image,
                               harvester_api_endpoints, keypair=keypair))
    vms.append(utils.create_vm(request, admin_session, opensuse_image,
                               harvester_api_endpoints, keypair=keypair))
    vms.append(utils.create_vm(request, admin_session, windows_image,
                               harvester_api_endpoints, keypair=keypair))
    yield vms
    if not request.config.getoption('--do-not-cleanup'):
        for vm_json in vms:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.mark.parametrize(
    'image',
    [
        ('http://cloud-images.ubuntu.com/releases/focal/release/'
         'ubuntu-20.04-server-cloudimg-amd64-disk-kvm.img'),
        ('https://github.com/rancher/k3os/releases/download/v0.20.4-k3s1r0/'
         'k3os-amd64.iso'),
        ('https://download.opensuse.org/tumbleweed/iso/'
         'openSUSE-Tumbleweed-NET-x86_64-Current.iso')
    ],
    indirect=True)
@pytest.mark.singlevmtest
def test_create_single_vm(admin_session, image, single_vm,
                          harvester_api_endpoints):
    # make sure the VM instance is successfully created
    utils.lookup_vm_instance(
        admin_session, harvester_api_endpoints, single_vm)
    # TODO(gyee): make sure we can ssh into the VM since we have the networking
    # part figure out (i.e. ensoure the vlan is publicly routable)


@pytest.mark.singlevmtest
def test_create_windows_vm(admin_session, image, windows_vm,
                           harvester_api_endpoints):
    # make sure the VM instance is successfully created
    utils.lookup_vm_instance(
        admin_session, harvester_api_endpoints, windows_vm)
    # TODO(gyee): make sure we can ssh into the VM since we have the networking
    # part figure out (i.e. ensoure the vlan is publicly routable)


@pytest.mark.multivmtest
def test_create_multiple_vms(admin_session, image, multiple_vms,
                             harvester_api_endpoints):
    # make sure all the VM instances are successfully created
    for a_vm in multiple_vms:
        utils.lookup_vm_instance(admin_session, harvester_api_endpoints, a_vm)
    # TODO(gyee): make sure we can ssh into the VM since we have the networking
    # part figure out (i.e. ensoure the vlan is publicly routable)


def test_create_vm_overcommit_cpu_and_memory_failed(
        request, admin_session, image, keypair, harvester_api_endpoints):
    # create the VM
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair, cpu=10000, memory_gb=10000,
                              running=False)
    vm_name = vm_json['metadata']['name']
    try:
        # now try to start the instance
        resp = admin_session.post(harvester_api_endpoints.start_vm % (vm_name))
        assert resp.status_code == 204, 'Failed to start VM instance %s' % (
            vm_name)
        # expect the VM to be unschedulable
        utils.assert_vm_unschedulable(request, admin_session,
                                      harvester_api_endpoints, vm_name)
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            resp = admin_session.get(
                harvester_api_endpoints.get_vm % (vm_name))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


def test_create_vm_overcommit_cpu_failed(
        request, admin_session, image, keypair, harvester_api_endpoints):
    # create the VM
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair, cpu=10000, memory_gb=1,
                              running=False)
    vm_name = vm_json['metadata']['name']
    try:
        # now try to start the instance
        resp = admin_session.post(harvester_api_endpoints.start_vm % (vm_name))
        assert resp.status_code == 204, 'Failed to start VM instance %s' % (
            vm_name)
        # expect the VM to be unschedulable
        utils.assert_vm_unschedulable(request, admin_session,
                                      harvester_api_endpoints, vm_name)
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            resp = admin_session.get(
                harvester_api_endpoints.get_vm % (vm_name))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


def test_create_vm_overcommit_memory_failed(
        request, admin_session, image, keypair, harvester_api_endpoints):
    # create the VM
    vm_json = utils.create_vm(request, admin_session, image,
                              harvester_api_endpoints,
                              keypair=keypair, cpu=1, memory_gb=10000,
                              running=False)
    vm_name = vm_json['metadata']['name']
    try:
        # now try to start the instance
        resp = admin_session.post(harvester_api_endpoints.start_vm % (vm_name))
        assert resp.status_code == 204, 'Failed to start VM instance %s' % (
            vm_name)
        # expect the VM to be unschedulable
        utils.assert_vm_unschedulable(request, admin_session,
                                      harvester_api_endpoints, vm_name)
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            resp = admin_session.get(
                harvester_api_endpoints.get_vm % (vm_name))
        if resp.status_code != 404:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


def test_create_vm_do_not_start(request, admin_session, image, keypair,
                                harvester_api_endpoints):
    created = False
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair,
                                  running=False)
        created = True
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            vm_json['metadata']['name']))
        assert resp.status_code == 404, (
            'Failed to create a VM with do not start: %s' % (resp.content))
    finally:
        if created:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


def test_create_update_vm_machine_type(request, admin_session, image, keypair,
                                       harvester_api_endpoints):
    created = False
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair,
                                  machine_type='pc')
        created = True
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            vm_json['metadata']['name']))
        machine = vm_json['spec']['template']['spec']['domain']['machine']
        assert machine['type'] == 'pc'
        vm_name = vm_json['metadata']['name']
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        previous_uid = vm_instance_json['metadata']['uid']
        # Update Machine Type to q35
        domain = vm_json['spec']['template']['spec']['domain']
        domain['machine']['type'] = 'q35'
        resp = utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            vm_json,
            harvester_api_endpoints.get_vm % (vm_name))
        # restart the VM instance for the updated machine type to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_name))
        updated_vm_data = resp.json()
        updated_machine_data = (
            updated_vm_data['spec']['template']['spec']['domain']['machine'])
        assert updated_machine_data['type'] == 'q35'
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            if created:
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints, vm_json)

# NOTE: the multi_node_scheduling test cases are designed to test
# scenarios where nodes may have different hardware configurations in
# terms of CPU, memory, and disk sizes. A VM with certain CPU requirement
# should only be scheduled on the nodes that satisfies those requirements.
# Likewise, it should schedule VMs on the nodes that has enough memory to
# satisfy the VM memory requirement.
#
# TODO(gyee): we may need to adjust these test cases if Kubernetes allows
# CPU and memory overcommit.


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
@pytest.mark.multi_node_scheduling
def test_create_vm_on_available_cpu_node(request, admin_session, image,
                                         keypair, harvester_api_endpoints):
    # find out the node that has the most available CPU
    (nodes, available_cpu) = utils.lookup_hosts_with_most_available_cpu(
        admin_session, harvester_api_endpoints)
    # now create a VM using the most available CPU to ensure it will only be
    # scheduled on the host that has that resource
    assert available_cpu > 0, 'No nodes has enough CPU available to create VMs'
    vm_json = None
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair,
                                  cpu=available_cpu)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node = vm_instance_json['status']['nodeName']
        assert vm_node in nodes, (
            'Expect VM to be running on nodes %s, but it is running on node '
            '%s' % (nodes, vm_node))
    finally:
        if vm_json:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
@pytest.mark.multi_node_scheduling
def test_update_vm_on_available_cpu_node(request, admin_session, image,
                                         keypair, harvester_api_endpoints):
    # find out the node that has the most available CPU
    (nodes, available_cpu) = utils.lookup_hosts_with_most_available_cpu(
        admin_session, harvester_api_endpoints)
    assert available_cpu > 0, 'No nodes has enough CPU available to create VMs'
    vm_json = None
    try:
        # first create a vanilla VM with minimal CPU and memory
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        # now update it use largest amount of CPU possible so that only the
        # largest CPU node can satisfy
        vm_name = vm_json['metadata']['name']
        previous_uid = vm_instance_json['metadata']['uid']
        domain_data = vm_json['spec']['template']['spec']['domain']
        domain_data['cpu']['cores'] = available_cpu
        utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            vm_json,
            harvester_api_endpoints.get_vm % (vm_name))
        # make sure the VM is restarted for the changes to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        # make sure it's now running on the nodes that has enough memory
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node = vm_instance_json['status']['nodeName']
        assert vm_node in nodes, (
            'Expect VM to be running on node %s, but it is running on node '
            '%s' % (nodes, vm_node))
    finally:
        if vm_json:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
@pytest.mark.multi_node_scheduling
def test_create_vm_on_available_memory_node(request, admin_session, image,
                                            keypair, harvester_api_endpoints):
    # find out the node that has the most available memory
    (nodes, available_memory) = utils.lookup_hosts_with_most_available_memory(
        admin_session, harvester_api_endpoints)
    # now create a VM using the most available memory to ensure it will only be
    # scheduled on the host that has that resource
    assert available_memory > 0, 'No nodes has enough memory to create VMs'
    vm_json = None
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair,
                                  memory_gb=available_memory)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node = vm_instance_json['status']['nodeName']
        assert vm_node in nodes, (
            'Expect VM to be running on node %s, but it is running on node '
            '%s' % (nodes, vm_node))
    finally:
        if vm_json:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
@pytest.mark.multi_node_scheduling
def test_update_vm_on_available_memory_node(request, admin_session, image,
                                            keypair, harvester_api_endpoints):
    # find out the node that has the most available memory
    (nodes, available_memory) = utils.lookup_hosts_with_most_available_memory(
        admin_session, harvester_api_endpoints)
    assert available_memory > 0, 'No nodes has enough memory to create VMs'
    vm_json = None
    try:
        # first create a vanilla VM with minimal CPU and memory
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        # now update it use largest amount of memory possible so that only the
        # largest memory node can satisfy
        vm_name = vm_json['metadata']['name']
        previous_uid = vm_instance_json['metadata']['uid']
        domain_data = vm_json['spec']['template']['spec']['domain']
        domain_data['resources']['requests']['memory'] = '%sGi' % (
            available_memory)
        utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            vm_json,
            harvester_api_endpoints.get_vm % (vm_name))
        # make sure the VM is restarted for the changes to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))
        # make sure it's now running on the nodes that has enough memory
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node = vm_instance_json['status']['nodeName']
        assert vm_node in nodes, (
            'Expect VM to be running on node %s, but it is running on node '
            '%s' % (nodes, vm_node))
    finally:
        if vm_json:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
@pytest.mark.multi_node_scheduling
def test_create_vm_on_available_cpu_and_memory_nodes(request, admin_session,
                                                     image, keypair,
                                                     harvester_api_endpoints):
    # TODO(gyee): should we make CPU and memory configurable?
    nodes = utils.lookup_hosts_with_cpu_and_memory(
        admin_session, harvester_api_endpoints, 2, 4)
    assert len(nodes) > 0, ('No nodes available to create VM with 2 CPU and '
                            '4GB memory')
    vm_json = None
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair,
                                  cpu=2, memory_gb=4)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node = vm_instance_json['status']['nodeName']
        assert vm_node in nodes, (
            'Expect VM to be running on node %s, but it is running on node '
            '%s' % (nodes, vm_node))
    finally:
        if vm_json:
            utils.delete_vm(request, admin_session, harvester_api_endpoints,
                            vm_json)


def test_host_maintenance_mode(request, admin_session, image, keypair,
                               harvester_api_endpoints):
    vm_json = None
    try:
        vm_json = utils.create_vm(request, admin_session, image,
                                  harvester_api_endpoints, keypair=keypair)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node_before_migrate = vm_instance_json['status']['nodeName']

        resp = admin_session.get(harvester_api_endpoints.get_node % (
            vm_node_before_migrate))
        host_json = resp.json()
        resp = admin_session.post(
            host_json['actions']['enableMaintenanceMode'])
        assert resp.status_code == 204, (
            'Failed to update node: %s' % (resp.content))
        utils.poll_for_resource_ready(request, admin_session,
                                      harvester_api_endpoints.get_node % (
                                          vm_node_before_migrate))
        resp = admin_session.get(harvester_api_endpoints.get_node % (
            vm_node_before_migrate))
        resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
        hdata = resp.json()
        assert hdata["spec"]["unschedulable"]
        s = hdata["metadata"]["annotations"]["harvesterhci.io/maintain-status"]
        assert s in ["running", "completed"]

        # give it some time for the VM to migrate
        time.sleep(120)

        def _check_vm_instance_migrated():
            resp = admin_session.get(
                harvester_api_endpoints.get_vm_instance % (
                    vm_json['metadata']['name']))
            if resp.status_code == 200:
                resp_json = resp.json()
                if ('status' in resp_json and
                        resp_json['status']['migrationState']['completed']):
                    return True
            return False

        success = polling2.poll(
            _check_vm_instance_migrated,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Timed out while waiting for VM to be migrated: %s' % (
            vm_json['metadata']['name'])

        vmi_json_after_migrate = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        vm_node_after_migrate = vmi_json_after_migrate['status']['nodeName']
        assert vm_node_after_migrate != vm_node_before_migrate
        resp = admin_session.get(harvester_api_endpoints.get_node % (
            vm_node_before_migrate))
        host_json = resp.json()
        resp = admin_session.post(
            host_json['actions']['disableMaintenanceMode'])
        assert resp.status_code == 204, (
            'Failed to update node: %s' % (resp.content))
        # migrate VM back to old host
        resp = admin_session.post(harvester_api_endpoints.migrate_vm % (
            vm_json['metadata']['name']),
            json={"nodeName": vm_node_before_migrate})
        assert resp.status_code == 204, 'Failed to migrat VM %s to host %s' % (
            vm_json['metadata']['name'], vm_node_before_migrate)
        # give it some time for the VM to migrate
        time.sleep(120)
        success = polling2.poll(
            _check_vm_instance_migrated,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Timed out as waiting for VM to migrate back: %s' % (
            vm_json['metadata']['name'])
        vmi_json_after_migrate = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_json)
        orig_node_name = vmi_json_after_migrate['status']['nodeName']
        assert orig_node_name == vm_node_before_migrate
    finally:
        if not request.config.getoption('--do-not-cleanup'):
            if vm_json:
                utils.delete_vm(request, admin_session,
                                harvester_api_endpoints, vm_json)
