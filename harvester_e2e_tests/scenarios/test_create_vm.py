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


pytest_plugins = [
   'harvester_e2e_tests.fixtures.image',
   'harvester_e2e_tests.fixtures.keypair',
   'harvester_e2e_tests.fixtures.volume',
  ]


@pytest.fixture()
def basic_vm(request, admin_session, image, keypair, volume,
             harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_vm',
        image_namespace=image['metadata']['namespace'],
        image_name=image['metadata']['name'],
        disk_size_gb=10,
        ssh_key_name=keypair['metadata']['name'],
        cpu=1,
        memory_gb=1,
        ssh_public_key=keypair['spec']['publicKey']
    )
    resp = admin_session.post(harvester_api_endpoints.create_vm,
                              json=request_json)
    assert resp.status_code == 201, 'Failed to create VM'
    vm_resp_json = resp.json()
    yield vm_resp_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_vm % (
                vm_resp_json['metadata']['name']))


def test_create_vm(admin_session, basic_vm, keypair, harvester_api_endpoints):
    ready = False
    # VM startup is asynchronous so make sure it is running and it has a
    # corresponding instance.
    retries = 10
    while retries:
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            basic_vm['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and 'ready' in resp_json['status'] and
                    resp_json['status']['ready']):
                ready = True
                break
        retries -= 1
        # TODO(gyee): should we make the sleep time configurable?
        time.sleep(30)
    assert ready, 'Timed out while waiting for VM to be ready.'
    # NOTE(gyee): seem like the corresponding VM instance has the same name as
    # the VM. If this assumption is not true, we need to fix this code.
    resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 200, 'Failed to lookup VM instance %s' % (
        basic_vm['metadata']['name'])
    # TODO(gyee): need to make sure we can SSH into the VM, but only
    # if the VM has a public IP.
