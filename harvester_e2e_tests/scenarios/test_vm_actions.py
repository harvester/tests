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
import time
import json

pytest_plugins = [
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.vm',
    'harvester_e2e_tests.fixtures.volume'
]


class TestVMActions:

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
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))

    def test_stop_vm(self, request, admin_session, harvester_api_endpoints,
                     basic_vm):
        resp = admin_session.put(harvester_api_endpoints.stop_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 202, 'Failed to stop VM instance %s' % (
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
        resp = admin_session.put(harvester_api_endpoints.start_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 202, (
            'Failed to start VM instance %s: %s' % (
                basic_vm['metadata']['name'], resp.content))

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
        resp = admin_session.put(harvester_api_endpoints.pause_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 200, 'Failed to pause VM instance %s' % (
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
        resp = admin_session.put(harvester_api_endpoints.unpause_vm % (
            basic_vm['metadata']['name']))
        assert resp.status_code == 200, 'Failed to unpause VM instance %s' % (
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
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        previous_uid = vm_instance_json['metadata']['uid']
        domain_data = basic_vm['spec']['template']['spec']['domain']
        updated_cores = domain_data['cpu']['cores'] + 1
        domain_data['cpu']['cores'] = updated_cores

        resp = utils.poll_for_update_resource(
            request, admin_session,
            harvester_api_endpoints.update_vm % (vm_name),
            basic_vm,
            harvester_api_endpoints.get_vm % (vm_name))
        updated_vm_data = resp.json()
        updated_domain_data = (
            updated_vm_data['spec']['template']['spec']['domain'])
        assert updated_domain_data['cpu']['cores'] == updated_cores
        # restart the VM instance for the changes to take effect
        utils.restart_vm(admin_session, harvester_api_endpoints, previous_uid,
                         vm_name, request.config.getoption('--wait-timeout'))


class TestVMVolumes:

    def test_create_vm_with_external_volume(self, admin_session,
                                            harvester_api_endpoints,
                                            vm_with_volume):
        # make sure the VM instance is successfully created
        utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm_with_volume)
        # make sure it's data volumes are in-use
        volumes = vm_with_volume['spec']['template']['spec']['volumes']
        for volume in volumes:
            resp = admin_session.get(harvester_api_endpoints.get_volume % (
                volume['persistentVolumeClaim']['claimName']))
            assert resp.status_code == 200, (
                'Failed to lookup volume %s: %s' % (
                    volume['persistentVolumeClaim']['claimName'],
                    resp.content))
            volume_json = resp.json()
            owned_by = json.loads(
                volume_json['metadata']['annotations'].get(
                    'harvesterhci.io/owned-by'))
            expected_owner = '%s/%s' % (
                vm_with_volume['metadata']['namespace'],
                vm_with_volume['metadata']['name'])
            # make sure VM is one of the owners
            found = False
            for owner in owned_by:
                if (owner['schema'] == 'kubevirt.io.virtualmachine' and
                        expected_owner in owner['refs']):
                    found = True
                    break
            assert found, ('Expecting %s to be in volume %s owners list' % (
                expected_owner, volume['persistentVolumeClaim']['claimName']))

    def test_delete_volume_in_use(self, request, admin_session,
                                  harvester_api_endpoints, vm_with_volume):
        volumes = vm_with_volume['spec']['template']['spec']['volumes']
        for volume in volumes:
            # try to delete a volume in 'in-use' state and it should
            # fail
            resp = admin_session.delete(
                harvester_api_endpoints.delete_volume % (
                    volume['persistentVolumeClaim']['claimName']))
            assert resp.status_code not in [200, 201], (
                'Deleting "in-use" volumes should not be permitted: %s' % (
                    resp.content))

    def test_delete_vm_then_volumes(self, request, admin_session,
                                    harvester_api_endpoints,
                                    vm_with_volume, volume):
        # delete the VM but keep the volumes
        utils.delete_vm(request, admin_session, harvester_api_endpoints,
                        vm_with_volume, remove_all_disks=False)
        volumes = vm_with_volume['spec']['template']['spec']['volumes']
        for data_vol in volumes:
            volume_name = data_vol['persistentVolumeClaim']['claimName']
            resp = admin_session.get(harvester_api_endpoints.get_volume % (
                volume_name))
            assert resp.status_code == 200, (
                'Failed to lookup data volume %s: %s' % (
                    volume_name, resp.content))
            # now cleanup the volume
            utils.delete_volume_by_name(request, admin_session,
                                        harvester_api_endpoints, volume_name)
