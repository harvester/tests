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
import polling2
import pytest
import time


pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair'
]


def _delete_vm(admin_session, harvester_api_endpoints, vm_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_vm % (
        vm_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Failed to delete VM %s: %s' % (
        vm_json['metadata']['name'], resp.content)


def _create_vm(admin_session, image, keypair, harvester_api_endpoints,
               cpu=1, disk_size_gb=10, memory_gb=1):
    request_json = utils.get_json_object_from_template(
        'basic_vm',
        image_namespace=image['metadata']['namespace'],
        image_name=image['metadata']['name'],
        disk_size_gb=disk_size_gb,
        ssh_key_name=keypair['metadata']['name'],
        cpu=cpu,
        memory_gb=memory_gb,
        ssh_public_key=keypair['spec']['publicKey']
    )
    resp = admin_session.post(harvester_api_endpoints.create_vm,
                              json=request_json)
    assert resp.status_code == 201, 'Failed to create VM'
    vm_resp_json = resp.json()
    # wait for VM to be ready
    time.sleep(30)

    def _check_vm_ready():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_resp_json['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and 'ready' in resp_json['status'] and
                    resp_json['status']['ready']):
                return True
        return False

    success = polling2.poll(
        _check_vm_ready,
        step=5,
        timeout=300)
    assert success, 'Timed out while waiting for VM to be ready.'
    return vm_resp_json


@pytest.fixture(scope='function')
def single_vm(request, admin_session, image, keypair, harvester_api_endpoints):
    vm_json = _create_vm(admin_session, image, keypair,
                         harvester_api_endpoints)
    yield vm_json
    if not request.config.getoption('--do-not-cleanup'):
        _delete_vm(admin_session, harvester_api_endpoints, vm_json)


# NOTE: we could have used the 'class' scope and use the code similar to
# above so we have multiple VMs running till class teardown. But we want to
# keep the tests clean so we are explicitly creating multiple VMs for a
# single test.
@pytest.fixture(scope='function')
def multiple_vms(request, admin_session, ubuntu_image, k3os_image,
                 opensuse_image, keypair, harvester_api_endpoints):
    vms = []
    vms.append(_create_vm(admin_session, ubuntu_image, keypair,
                          harvester_api_endpoints))
    vms.append(_create_vm(admin_session, k3os_image, keypair,
                          harvester_api_endpoints))
    vms.append(_create_vm(admin_session, opensuse_image, keypair,
                          harvester_api_endpoints))
    yield vms
    if not request.config.getoption('--do-not-cleanup'):
        for vm_json in vms:
            _delete_vm(admin_session, harvester_api_endpoints, vm_json)


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
def test_create_single_vm(admin_session, image, single_vm,
                          harvester_api_endpoints):
    # make sure the VM instance is successfully created
    utils.lookup_vm_instance(
        admin_session, harvester_api_endpoints, single_vm)
    # TODO(gyee): make sure we can ssh into the VM since we have the networking
    # part figure out (i.e. ensoure the vlan is publicly routable)


def test_create_multiple_vms(admin_session, image, multiple_vms,
                             harvester_api_endpoints):
    # make sure all the VM instances are successfully created
    for a_vm in multiple_vms:
        utils.lookup_vm_instance(admin_session, harvester_api_endpoints, a_vm)
    # TODO(gyee): make sure we can ssh into the VM since we have the networking
    # part figure out (i.e. ensoure the vlan is publicly routable)


# FIXME(gyee): skipping this test due to
# https://github.com/harvester/harvester/issues/174. Will need to re-enable it
# once the bug is addressed.
@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/174')
def test_create_vm_overcommit_cpu_and_memory_failed(
        admin_session, image, keypair, harvester_api_endpoints):
    # expect failure to create VM for CPU and memory overcommit
    _create_vm(admin_session, image, keypair, harvester_api_endpoints,
               cpu=10000, memory_gb=10000)
