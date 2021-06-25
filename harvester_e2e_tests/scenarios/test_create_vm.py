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
import json


pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.volume',
]


@pytest.fixture(scope='class', autouse=True)
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
        timeout=120)
    assert success, 'Timed out while waiting for VM to be ready.'
    yield vm_resp_json
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_vm % (
                vm_resp_json['metadata']['name']))


def lookup_vm_instance(admin_session, harvester_api_endpoints, basic_vm):
    # NOTE(gyee): seem like the corresponding VM instance has the same name as
    # the VM. If this assumption is not true, we need to fix this code.
    resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
        basic_vm['metadata']['name']))
    assert resp.status_code == 200, 'Failed to lookup VM instance %s' % (
        basic_vm['metadata']['name'])
    return resp.json()


def test_vm_actions(admin_session, basic_vm, keypair,
                    harvester_api_endpoints):
    # make sure the VM instance is successfully created
    vm_instance_json = lookup_vm_instance(
        admin_session, harvester_api_endpoints, basic_vm)

    # Test Various actions on created VM
#    _update_vm(admin_session, harvester_api_endpoints, basic_vm)
    _restart_vm(admin_session, harvester_api_endpoints, vm_instance_json)
    _stop_vm(admin_session, harvester_api_endpoints, vm_instance_json)
    _start_vm(admin_session, harvester_api_endpoints, vm_instance_json)
    _pause_vm(admin_session, harvester_api_endpoints, vm_instance_json)
    _unpause_vm(admin_session, harvester_api_endpoints, vm_instance_json)


def _restart_vm(admin_session, harvester_api_endpoints, basic_vm_instance):
    # restart the VM instance
    resp = admin_session.post(harvester_api_endpoints.restart_vm % (
        basic_vm_instance['metadata']['name']))
    assert resp.status_code == 204, 'Failed to restart VM instance %s' % (
        basic_vm_instance['metadata']['name'])

    # give it some time for the VM instance to restart
    time.sleep(30)
    previous_uid = basic_vm_instance['metadata']['uid']

    def _check_new_vm_instance_running():
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm_instance['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    'phase' in resp_json['status'] and
                    resp_json['status']['phase'] == 'Running' and
                    resp_json['metadata']['uid'] != previous_uid):
                return True
        return False

    success = polling2.poll(
        _check_new_vm_instance_running,
        step=5,
        timeout=120)
    assert success, 'Failed to restart VM instance %s' % (
        basic_vm['metadata']['name'])


def _stop_vm(admin_session, harvester_api_endpoints, basic_vm_instance):
    resp = admin_session.post(harvester_api_endpoints.stop_vm % (
        basic_vm_instance['metadata']['name']))
    assert resp.status_code == 204, 'Failed to stop VM instance %s' % (
        basic_vm_instance['metadata']['name'])

    # give it some time for the VM instance to stop
    time.sleep(30)

    def _check_vm_instance_stopped():
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm_instance['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_vm_instance_stopped,
        step=5,
        timeout=120)
    assert success, 'Failed to stop VM: %s' % (
        basic_vm_instance['metadata']['name'])


def _start_vm(admin_session, harvester_api_endpoints, basic_vm_instance):
    # NOTE: this step must be done after VM has stopped
    resp = admin_session.post(harvester_api_endpoints.start_vm % (
        basic_vm_instance['metadata']['name']))
    assert resp.status_code == 204, 'Failed to start VM instance %s' % (
        basic_vm_instance['metadata']['name'])

    # give it some time for the VM to start
    time.sleep(30)

    def _check_vm_instance_started():
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
            basic_vm_instance['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    resp_json['status']['phase'] == 'Running'):
                return True
        return False

    success = polling2.poll(
        _check_vm_instance_started,
        step=5,
        timeout=120)
    assert success, 'Failed to get VM instance for: %s' % (
        basic_vm['metadata']['name'])


def _pause_vm(admin_session, harvester_api_endpoints, basic_vm_instance):
    resp = admin_session.post(harvester_api_endpoints.pause_vm % (
        basic_vm_instance['metadata']['name']))
    assert resp.status_code == 204, 'Failed to pause VM instance %s' % (
        basic_vm_instance['metadata']['name'])

    # give it some time for the VM to pause
    time.sleep(10)

    def _check_vm_instance_paused():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            basic_vm_instance['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if 'status' in resp_json:
                for condition in resp_json['status']['conditions']:
                    if (condition['type'] == 'Paused' and
                            condition['status'] == 'True'):
                        return True
        return False

    success = polling2.poll(
        _check_vm_instance_paused,
        step=5,
        timeout=120)
    assert success, 'Timed out while waiting for VM to be paused.'


def _unpause_vm(admin_session, harvester_api_endpoints, basic_vm_instance):
    # NOTE: make sure to execute this step after _paused_vm()
    resp = admin_session.post(harvester_api_endpoints.unpause_vm % (
        basic_vm_instance['metadata']['name']))
    assert resp.status_code == 204, 'Failed to unpause VM instance %s' % (
        basic_vm_instance['metadata']['name'])

    # give it some time to unpause
    time.sleep(10)

    def _check_vm_instance_unpaused():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            basic_vm_instance['metadata']['name']))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and 'ready' in resp_json['status'] and
                    resp_json['status']['ready']):
                return True
        return False

    success = polling2.poll(
        _check_vm_instance_unpaused,
        step=5,
        timeout=120)
    assert success, 'Timed out while waiting for VM to be unpaused.'


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
