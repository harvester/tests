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
import json

pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.volume',
]


@pytest.fixture(scope='class')
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
    vmi_resp_json = resp.json()
    vmiUID = vmi_resp_json['metadata']['uid']

    # TODO(gyee): need to make sure we can SSH into the VM, but only
    # if the VM has a public IP.

    # Test Various actions on created VM
#    _update_vm(admin_session, harvester_api_endpoints, basic_vm)
    _restart_vm(admin_session, harvester_api_endpoints,
                basic_vm, vmiUID)
    _stop_vm(admin_session, harvester_api_endpoints, basic_vm)
    _start_vm(admin_session, harvester_api_endpoints, basic_vm)
    _pause_vm(admin_session, harvester_api_endpoints, basic_vm)
    _unpause_vm(admin_session, harvester_api_endpoints, basic_vm)


def _restart_vm(admin_session, harvester_api_endpoints, basic_vm, vmiid):
    resp = admin_session.post(harvester_api_endpoints.restart_vm % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 204, 'Failed to restart VM instance %s' % (
        basic_vm['metadata']['name'])

    retries = 20
    while retries:
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    resp_json['status']['phase'] == 'Running' and
                    resp_json['metadata']['uid'] != vmiid):
                vmiUID = resp_json['metadata']['uid']
                break

        time.sleep(30)
        retries -= 1

    assert resp.status_code == 200, 'Failed to get VM instance %s' % (
        basic_vm['metadata']['name'])
    assert vmiid != vmiUID, 'VM instance not changed for %s' % (
        basic_vm['metadata']['name'])


def _stop_vm(admin_session, harvester_api_endpoints, basic_vm):
    resp = admin_session.post(harvester_api_endpoints.stop_vm % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 204, 'Failed to stop VM instance %s' % (
        basic_vm['metadata']['name'])

    retries = 10
    while retries:
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm['metadata']['name']))
        if resp.status_code == 200:
            time.sleep(5)
            retries -= 1
        else:
            break

    assert resp.status_code == 404, 'Found VM instance for: %s' % (
        basic_vm['metadata']['name'])


def _start_vm(admin_session, harvester_api_endpoints, basic_vm):
    resp = admin_session.post(harvester_api_endpoints.start_vm % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 204, 'Failed to start VM instance %s' % (
        basic_vm['metadata']['name'])

    retries = 10
    while retries:
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    resp_json['status']['phase'] == 'Running'):
                break

        time.sleep(5)
        retries -= 1

    assert resp.status_code == 200, 'Failed to get VM instance for: %s' % (
        basic_vm['metadata']['name'])


def _pause_vm(admin_session, harvester_api_endpoints, basic_vm):
    paused = False
    resp = admin_session.post(harvester_api_endpoints.pause_vm % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 204, 'Failed to pause VM instance %s' % (
        basic_vm['metadata']['name'])

    retries = 10
    while retries:
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            basic_vm['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    'Paused' in [i['type'] for i in
                                 resp_json['status']['conditions']] and
                    "True" in [i['status'] for i in
                               resp_json['status']['conditions']]):
                paused = True
                break
        retries -= 1
        # TODO(gyee): should we make the sleep time configurable?
        time.sleep(30)
    assert paused, 'Timed out while waiting for VM to be paused.'


def _unpause_vm(admin_session, harvester_api_endpoints, basic_vm):
    resp = admin_session.post(harvester_api_endpoints.unpause_vm % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 204, 'Failed to unpause VM instance %s' % (
        basic_vm['metadata']['name'])
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
    assert ready, 'Timed out while waiting for VM to be unpaused.'


def _update_vm(admin_session, harvester_api_endpoints, basic_vm):
    domain_data = basic_vm['spec']['template']['spec']['domain']
    domain_data['cpu']['cores'] = 2
    domain_data['resources']['requests']['memory'] = "2Gi"

    retries = 20
    while retries:
        resp = admin_session.put(harvester_api_endpoints.update_vm % (
            basic_vm['metadata']['name']), json=basic_vm)
        if (resp.status_code == 409 and
                'latest version and try' in resp.content.decode('utf-8')):
            time.sleep(30)
            retries -= 1
        else:
            break
    assert resp.status_code == 200, 'Failed to update vm: %s' % (
        resp.content)
    updated_vm = resp.json()
    updated_domain_data = json.loads(updated_vm['spec']['template']['spec']
                                     ['domain'])
    assert updated_domain_data['cpu']['cores'] == domain_data['cpu']['cores']
    assert (updated_domain_data['resources']['requests']['memory'] ==
            domain_data['resources']['requests']['memory'])
