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
import uuid


pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.network'
]


@pytest.fixture(scope='class')
def network_data():
    yaml_data = """#cloud-config
version: 1
config:
  - type: physical
    name: eth0
    subnets:
      - type: dhcp
  - type: physical
    name: eth1
    subnets:
      - type: dhcp
"""
    return yaml_data.replace('\n', '\\n')


@pytest.fixture(scope='class')
def user_data_with_guest_agent(keypair):
    # set to root user password to 'linux' to test password login in
    # addition to SSH login
    yaml_data = """#cloud-config
chpasswd:
  list: |
    root:linux
  expire: false
ssh_authorized_keys:
  - %s
package_update: true
packages:
  - qemu-guest-agent
runcmd:
  - - systemctl
    - enable
    - '--now'
    - qemu-guest-agent
""" % (keypair['spec']['publicKey'])
    return yaml_data.replace('\n', '\\n')


@pytest.fixture(scope='class')
def basic_vm(request, admin_session, image, user_data_with_guest_agent,
             network_data, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_vm',
        image_namespace=image['metadata']['namespace'],
        image_name=image['metadata']['name'],
        image_storage_class=image['status']['storageClassName'],
        disk_size_gb=10,
        cpu=1,
        memory_gb=1,
        network_data=network_data,
        user_data=user_data_with_guest_agent
    )
    resp = admin_session.post(harvester_api_endpoints.create_vm,
                              json=request_json)
    assert resp.status_code == 201, 'Failed to create VM: %s' % (
        resp.content)
    vm_resp_json = resp.json()
    # wait for VM to be ready
    time.sleep(120)

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
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for VM to be ready.'
    yield vm_resp_json
    if not request.config.getoption('--do-not-cleanup'):
        # cleanup both disks, image and cdrom
        params = {'removedDisks': 'disk-0,disk-1'}
        resp = admin_session.delete(
            harvester_api_endpoints.delete_vm % (
                vm_resp_json['metadata']['name']), params=params)


class TestVMActions:

    def _assert_vm_restarted(self, admin_session, harvester_api_endpoints,
                             previous_uid, vm_name, wait_timeout):
        # give it some time for the VM instance to restart
        time.sleep(120)

        def _check_vm_instance_restarted():
            resp = admin_session.get(
                harvester_api_endpoints.get_vm_instance % (vm_name))
            if resp.status_code == 200:
                resp_json = resp.json()
                if ('status' in resp_json and
                        'phase' in resp_json['status'] and
                        resp_json['status']['phase'] == 'Running' and
                        resp_json['metadata']['uid'] != previous_uid):
                    return True
            return False

        success = polling2.poll(
            _check_vm_instance_restarted,
            step=5,
            timeout=wait_timeout)
        assert success, 'Failed to restart VM %s' % (vm_name)

    def test_create_vm(self, admin_session, harvester_api_endpoints, basic_vm):
        # make sure the VM instance is successfully created
        utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        # make sure it has a cdrom device
        devices = basic_vm['spec']['template']['spec']['domain']['devices']
        disks = devices['disks']
        found_cdrom = False
        for disk in disks:
            if 'cdrom' in disk:
                found_cdrom = True
                break
        assert found_cdrom, 'Expecting "cdrom" in the disks list.'

    def test_restart_vm(self, request, admin_session, harvester_api_endpoints,
                        basic_vm):
        vm_name = basic_vm['metadata']['name']
        previous_uid = basic_vm['metadata']['uid']
        # restart the VM instance
        resp = admin_session.post(harvester_api_endpoints.restart_vm % (
            vm_name))
        assert resp.status_code == 204, 'Failed to restart VM instance %s' % (
            vm_name)
        self._assert_vm_restarted(admin_session, harvester_api_endpoints,
                                  previous_uid, vm_name,
                                  request.config.getoption('--wait-timeout'))

    def test_stop_vm(self, request, admin_session, harvester_api_endpoints,
                     basic_vm):
        resp = admin_session.post(harvester_api_endpoints.stop_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 204, 'Failed to stop VM instance %s' % (
            basic_vm['metadata']['name'])

        # give it some time for the VM instance to stop
        time.sleep(120)

        def _check_vm_instance_stopped():
            resp = admin_session.get(
                harvester_api_endpoints.get_vm_instance % (
                    basic_vm['metadata']['name']))
            if resp.status_code == 404:
                return True
            return False

        success = polling2.poll(
            _check_vm_instance_stopped,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Failed to stop VM: %s' % (
            basic_vm['metadata']['name'])

    def test_start_vm(self, request, admin_session, harvester_api_endpoints,
                      basic_vm):
        # NOTE: this step must be done after VM has stopped
        resp = admin_session.post(harvester_api_endpoints.start_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 204, 'Failed to start VM instance %s' % (
            basic_vm['metadata']['name'])

        # give it some time for the VM to start
        time.sleep(120)

        def _check_vm_instance_started():
            resp = admin_session.get(
                harvester_api_endpoints.get_vm_instance % (
                    basic_vm['metadata']['name']))
            if resp.status_code == 200:
                resp_json = resp.json()
                if ('status' in resp_json and
                        resp_json['status']['phase'] == 'Running'):
                    return True
            return False

        success = polling2.poll(
            _check_vm_instance_started,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Failed to get VM instance for: %s' % (
            basic_vm['metadata']['name'])

    def test_pause_vm(self, request, admin_session, harvester_api_endpoints,
                      basic_vm):
        resp = admin_session.post(harvester_api_endpoints.pause_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 204, 'Failed to pause VM instance %s' % (
            basic_vm['metadata']['name'])

        # give it some time for the VM to pause
        time.sleep(60)

        def _check_vm_instance_paused():
            resp = admin_session.get(harvester_api_endpoints.get_vm % (
                basic_vm['metadata']['name']))
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
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Timed out while waiting for VM to be paused.'

    def test_unpause_vm(self, request, admin_session, harvester_api_endpoints,
                        basic_vm):
        # NOTE: make sure to execute this step after _paused_vm()
        resp = admin_session.post(harvester_api_endpoints.unpause_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 204, 'Failed to unpause VM instance %s' % (
            basic_vm['metadata']['name'])

        # give it some time to unpause
        time.sleep(10)

        def _check_vm_instance_unpaused():
            resp = admin_session.get(harvester_api_endpoints.get_vm % (
                basic_vm['metadata']['name']))
            if resp.status_code == 200:
                resp_json = resp.json()
                if ('status' in resp_json and
                        'ready' in resp_json['status'] and
                        resp_json['status']['ready']):
                    return True
            return False

        success = polling2.poll(
            _check_vm_instance_unpaused,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Timed out while waiting for VM to be unpaused.'

    def test_update_vm_cpu(self, request, admin_session,
                           harvester_api_endpoints, basic_vm):
        vm_name = basic_vm['metadata']['name']
        previous_uid = basic_vm['metadata']['uid']
        domain_data = basic_vm['spec']['template']['spec']['domain']
        updated_cores = domain_data['cpu']['cores'] + 1
        domain_data['cpu']['cores'] = updated_cores

        resp = utils.poll_for_update_resource(
            admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            basic_vm,
            harvester_api_endpoints.get_vm % (vm_name))
        updated_vm_data = resp.json()
        updated_domain_data = (
            updated_vm_data['spec']['template']['spec']['domain'])
        assert updated_domain_data['cpu']['cores'] == updated_cores
        self._assert_vm_restarted(admin_session, harvester_api_endpoints,
                                  previous_uid, vm_name,
                                  request.config.getoption('--wait-timeout'))

    @pytest.mark.public_network
    def test_update_vm_network(self, request, admin_session,
                               harvester_api_endpoints, basic_vm, network):
        vm_name = basic_vm['metadata']['name']
        previous_uid = basic_vm['metadata']['uid']
        # add a new network to the VM
        network_name = 'nic-%s' % uuid.uuid4().hex[:5]
        new_network = {
            'name': network_name,
            'multus': {'networkName': network['metadata']['name']}
        }
        new_network_interface = {
            'bridge': {},
            'model': 'virtio',
            'name': network_name
        }
        spec = basic_vm['spec']['template']['spec']
        if 'interfaces' not in spec['domain']['devices']:
            spec['domain']['devices']['interfaces'] = []
        spec['domain']['devices']['interfaces'].append(new_network_interface)
        if 'networks' not in spec:
            spec['networks'] = []
        spec['networks'].append(new_network)
        resp = utils.poll_for_update_resource(
            admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            basic_vm,
            harvester_api_endpoints.get_vm % (vm_name))
        updated_vm_data = resp.json()
        self._assert_vm_restarted(admin_session, harvester_api_endpoints,
                                  previous_uid, vm_name,
                                  request.config.getoption('--wait-timeout'))

        found = False
        # check to make sure the network device is in the updated spec
        updated_spec = updated_vm_data['spec']['template']['spec']
        for i in updated_spec['domain']['devices']['interfaces']:
            if (network_name == i['name'] and i['model'] == 'virtio' and
                    'bridge' in i):
                found = True
                break
        assert found, 'Failed to add new network device to VM %s' % (vm_name)
        # check to make sure network is in the updated spec
        found = False
        for n in updated_spec['networks']:
            if network_name == n['name']:
                found = True
                break
        assert found, 'Failed to add new network to VM %s' % (vm_name)
        # TODO(gyee): 1) make sure the new interface got an IP; and
        # 2) make sure we can ping that IP if it has a port in a public router
