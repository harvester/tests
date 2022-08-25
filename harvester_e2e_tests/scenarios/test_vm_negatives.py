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

import pytest
import polling2

from harvester_e2e_tests import utils


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
        node_state = dict()

        def _wait_for_node_unavailble():
            resp = admin_session.get(harvester_api_endpoints.get_node % node_name)
            if resp.status_code == 200:
                nonlocal node_state
                node_state = resp.json()['metadata']['state']
                return node_state['name'] == "unavailable" and node_state['error']

        # make sure the VM instance is successfully created
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)
        # abruptly shutdown the node where it is running
        node_name = vm_instance_json['status']['nodeName']
        utils.power_off_node(request, admin_session, harvester_api_endpoints,
                             node_name)
        try:
            polling2.poll(_wait_for_node_unavailble, step=5,
                          timeout=request.config.getoption('--wait-timeout'))
        except polling2.TimeoutException:
            raise AssertionError(f"`{node_name}` node has been poweroff but"
                                 " its status not changed.\n"
                                 f"{node_state!r}")

        # See https://github.com/harvester/harvester/issues/982
        vm_instance_json = utils.lookup_vm_instance(
            admin_session, harvester_api_endpoints, basic_vm)

        found = None
        for condition in vm_instance_json['status']['conditions']:
            if condition['type'] == 'Ready':
                assert condition['status'] == 'False', (
                    "Unexpected condition:"
                    f"type={condition['type']!r}, status={condition['status']!r}"
                    f"\n{condition!r}")
                found = condition
                break

        assert found is not None, (
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
