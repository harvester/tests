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

import copy
from harvester_e2e_tests import utils
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.session',
]


@pytest.mark.hosts_p1
@pytest.mark.p1
def test_get_host(admin_session, harvester_cluster_nodes,
                  harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-02-Test to get host
    """
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    assert len(host_data['data']) == harvester_cluster_nodes


@pytest.mark.hosts_p1
@pytest.mark.p1
@pytest.mark.hosts_p2
@pytest.mark.p2
def test_verify_host_maintenance_mode(request, admin_session,
                                      harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-03-Verify Enabling maintenance mode
        hosts-12-Host with no VMs on it
    """
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    # NOTE: always test on the first node for now
    node_json = host_data['data'][0]
    node_name = node_json['metadata']['name']
    utils.enable_maintenance_mode(request, admin_session,
                                  harvester_api_endpoints, node_json)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host %s: %s' % (
        node_name, resp.content)
    node_json = resp.json()
    assert node_json["spec"]["unschedulable"]
    s = node_json["metadata"]["annotations"]["harvesterhci.io/maintain-status"]
    assert s in ["running", "completed"]
    utils.disable_maintenance_mode(request, admin_session,
                                   harvester_api_endpoints, node_json)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host %s: %s' % (
        node_name, resp.content)
    node_json = resp.json()
    assert "unschedulable" not in node_json["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            node_json["metadata"]["annotations"])


@pytest.mark.hosts_p1
@pytest.mark.p1
def test_update_first_node(request, admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-04-Edit Config Add description and other details
    """
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    first_node = host_data['data'][0]
    original_annotations = copy.deepcopy(first_node['metadata']['annotations'])
    first_node['metadata']['annotations'] = {
        'field.cattle.io/description': 'for-test-update',
        'harvesterhci.io/host-custom-name': 'for-test-update'
    }
    try:
        resp = utils.poll_for_update_resource(
            request, admin_session,
            host_data['data'][0]['links']['update'],
            first_node,
            harvester_api_endpoints.get_node % (host_data['data'][0]['id']))
        updated_host_data = resp.json()
        assert updated_host_data['metadata']['annotations'].get(
            'field.cattle.io/description') == 'for-test-update'
        assert updated_host_data['metadata']['annotations'].get(
            'harvesterhci.io/host-custom-name') == 'for-test-update'
    finally:
        # change it back to original
        if updated_host_data:
            updated_host_data['metadata']['annotations'] = original_annotations
            utils.poll_for_update_resource(
                request, admin_session,
                updated_host_data['links']['update'],
                updated_host_data,
                harvester_api_endpoints.get_node % (updated_host_data['id']))


@pytest.mark.hosts_p1
@pytest.mark.p1
def test_update_using_yaml(request, admin_session, harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-05-Edit through Yaml
    """
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    first_node = host_data['data'][0]
    original_annotations = copy.deepcopy(first_node['metadata']['annotations'])
    first_node['metadata']['annotations'] = {
        'field.cattle.io/description': 'for-yaml-update',
        'harvesterhci.io/host-custom-name': 'for-yaml-update'
    }
    try:
        resp = utils.poll_for_update_resource(
            request, admin_session,
            host_data['data'][0]['links']['update'],
            first_node,
            harvester_api_endpoints.get_node % (host_data['data'][0]['id']),
            use_yaml=True)
        updated_host_data = resp.json()
        assert updated_host_data['metadata']['annotations'].get(
            'field.cattle.io/description') == 'for-yaml-update'
        assert updated_host_data['metadata']['annotations'].get(
            'harvesterhci.io/host-custom-name') == 'for-yaml-update'
    finally:
        # change it back to original
        if updated_host_data:
            updated_host_data['metadata']['annotations'] = original_annotations
            utils.poll_for_update_resource(
                request, admin_session,
                updated_host_data['links']['update'],
                updated_host_data,
                harvester_api_endpoints.get_node % (updated_host_data['id']))


@pytest.mark.trylast
@pytest.mark.delete_host
@pytest.mark.hosts_p1
@pytest.mark.p1
def test_delete_host(request, admin_session, harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-07-Delete the host
    """
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()

    if len(host_data["data"]) == 1:
        pytest.skip("It will break the cluster as it is single node.")

    # FIXME(gyee): for now only delete the last node in the cluster due to
    # https://github.com/harvester/harvester/issues/1398
    # This is assuming that the orders are correct. We'll need to test
    # deleting the first node after the issue's been resolved.
    host_data_to_delete = host_data['data'][-1]
    # delete the host
    utils.delete_host(request, admin_session, harvester_api_endpoints,
                      host_data_to_delete)
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    assert host_data_to_delete not in host_data['data']
    # TODO(gyee): do we need to make sure the VIP still works?


@pytest.mark.hosts_p1
@pytest.mark.p1
@pytest.mark.host_management
def test_host_mgmt_maintenance_mode(request, admin_session,
                                    harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-13-Maintenance Mode-turn off host that is in maintenance mode
        hosts-14-Maintenance Mode-Start host that is in maintenance mode
        hosts-16-Maintenance Mode-Take host out of maintenance mode that
        has not been rebooted
    """
    # Power Off Node
    host_info = utils.poweroff_host_maintenance_mode(request, admin_session,
                                                     harvester_api_endpoints)
    node_name = host_info['id']
    # power On Node
    utils.power_on_node(request, admin_session, harvester_api_endpoints,
                        node_name)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "Ready,SchedulingDisabled" in ret_data["metadata"]["fields"]
    # Disable Maintenance Mode
    utils.disable_maintenance_mode(request, admin_session,
                                   harvester_api_endpoints, ret_data)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            ret_data["metadata"]["annotations"])


@pytest.mark.hosts_p1
@pytest.mark.p1
@pytest.mark.host_management
def test_host_reboot_maintenance_mode(request, admin_session,
                                      harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-17-Maintenance Mode-Take host out of maintenance
        mode that has been rebooted
        hosts-15-Maintenance Mode-reboot host that is in
        maintenance mode
        hosts-02-Negative test-Verify the state for Powered down node
    """
    # Power Off Node
    host_info = utils.poweroff_host_maintenance_mode(request, admin_session,
                                                     harvester_api_endpoints)
    node_name = host_info['id']
    # Reboot Node
    utils.reboot_node(request, admin_session, harvester_api_endpoints,
                      node_name)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "Ready,SchedulingDisabled" in ret_data["metadata"]["fields"]
    # Disable Maintenance Mode
    utils.disable_maintenance_mode(request, admin_session,
                                   harvester_api_endpoints, ret_data)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            ret_data["metadata"]["annotations"])


@pytest.mark.hosts_p1
@pytest.mark.p1
@pytest.mark.host_management
def test_host_poweroff_state(request, admin_session,
                             harvester_api_endpoints):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-01-Negative test-Verify the state for Powered down node
    """
    host_of = utils.lookup_host_not_harvester_endpoint(request, admin_session,
                                                       harvester_api_endpoints)
    try:
        # Power off Node
        node_name = host_of['id']
        utils.power_off_node(request, admin_session, harvester_api_endpoints,
                             node_name)
        resp = admin_session.get(
            harvester_api_endpoints.get_node % (node_name))
        resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
        ret_data = resp.json()
        assert ret_data["metadata"]["state"]["name"] in [
            "in-progress", "unavailable"]
    finally:
        # power On Node
        utils.power_on_node(request, admin_session, harvester_api_endpoints,
                            node_name)
        resp = admin_session.get(
            harvester_api_endpoints.get_node % (node_name))
        resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
        ret_data = resp.json()
        assert ret_data["metadata"]["state"]["name"] == "active"
