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

pytest_plugins = [
    'harvester_e2e_tests.fixtures.vm'
]


class TestHostDown:
    @pytest.mark.virtual_machines_p1
    @pytest.mark.p1
    @pytest.mark.host_management
    def test_host_shutdown(self, request, admin_session,
                           harvester_api_endpoints, basic_vm):
        """
        Test shutdown when vm is running and start vm
        Covers:
            Negative virtual-machines-03-Start VM Negative
        """
        # make sure the VM instance is successfully created
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        # abruptly shutdown the node where it is running
        node_name = vm_instance_json['status']['nodeName']
        utils.power_off_node(request, admin_session, harvester_api_endpoints,
                             node_name)
        # FIXME(gyee): we currently don't know what the expected behavoir is
        # for an instance where the node is abruptly shutdown. I would've
        # expected the instance to go into error state. But that doesn't seem
        # to be the case right now. It seem to get stuck on "PodTerminating".
        #
        # See https://github.com/harvester/harvester/issues/913
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        found = False
        for condition in vm_instance_json['status']['conditions']:
            if condition['type'] == 'Ready':
                assert condition['status'] == 'False', (
                    'Expecting "False" status, got %s instead' % (
                        condition['status']))
                # FIXME(gyee): is 'reason' always present?
                # assert condition['reason'] == 'PodTerminating', (
                #    'Expecting "PodTerminating" in reason, got %s instead' % (
                #        condition['reason']))
                found = True
                break
        assert found, (
            'Expecting "PodTerminating" in conditions, got %s instead' % (
                vm_instance_json['status']['conditions']))
        # power-on the node
        utils.power_on_node(request, admin_session, harvester_api_endpoints,
                            node_name)

    @pytest.mark.skip("https://github.com/harvester/harvester/issues/2148")
    @pytest.mark.host_management
    @pytest.mark.virtual_machines_p1
    @pytest.mark.p1
    def test_delete_vm_while_host_shutdown(self, request, admin_session,
                                           harvester_api_endpoints, basic_vm):
        """
        Test shutdown when vm is running and delete vm
        Covers:
            Negative virtual-machines-05-Delete VM Negative
        """
        # make sure the VM instance is successfully created and running
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        utils.assert_vm_ready(request, admin_session, harvester_api_endpoints,
                              vm_instance_json["metadata"]["name"], True)

        # abruptly shutdown the node where it is running
        node_name = vm_instance_json['status']['nodeName']
        utils.power_off_node(request, admin_session, harvester_api_endpoints,
                             node_name)
        # now try to delete the VM while node is down, this should succeed
        utils.delete_vm(request, admin_session, harvester_api_endpoints,
                        basic_vm)
        # power-on the node
        utils.power_on_node(request, admin_session, harvester_api_endpoints,
                            node_name)

    @pytest.mark.host_management
    def test_vm_after_host_reboot(self, request, admin_session,
                                  harvester_api_endpoints, basic_vm):
        # make sure the VM instance is successfully created and running
        utils.assert_vm_ready(request, admin_session, harvester_api_endpoints,
                              basic_vm["metadata"]["name"], True)
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)

        node_name = vm_instance_json['status']['nodeName']
        # Reboot VM
        utils.reboot_node(request, admin_session, harvester_api_endpoints,
                          node_name)
        # VM restarted
        vm_name = basic_vm['metadata']['name']
        previous_uid = basic_vm['metadata']['uid']
        utils.assert_vm_restarted(admin_session, harvester_api_endpoints,
                                  previous_uid, vm_name,
                                  request.config.getoption('--wait-timeout'))
