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
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.session',
]


def test_get_host(admin_session, harvester_cluster_nodes,
                  harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    assert len(host_data['data']) == harvester_cluster_nodes


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/1021')
def test_verify_host_maintenance_mode(request, admin_session,
                                      harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    # NOTE: always test on the first node for now
    resp = admin_session.post(
        host_data['data'][0]['actions']['enableMaintenanceMode'])
    assert resp.status_code == 204, (
        'Failed to update node: %s' % (resp.content))
    utils.poll_for_resource_ready(request, admin_session,
                                  host_data['data'][0]['links']['view'])
    resp = admin_session.get(host_data['data'][0]['links']['view'])
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert ret_data["spec"]["unschedulable"]
    s = ret_data["metadata"]["annotations"]["harvesterhci.io/maintain-status"]
    assert s in ["running", "completed"]
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    ret_data = resp.json()
    resp = admin_session.post(
        ret_data['data'][0]['actions']['disableMaintenanceMode'])
    assert resp.status_code == 204, (
        'Failed to update node: %s' % (resp.content))
    resp = admin_session.get(host_data['data'][0]['links']['view'])
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            ret_data["metadata"]["annotations"])


def test_update_first_node(request, admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    first_node = host_data['data'][0]
    first_node['metadata']['annotations'] = {
        'field.cattle.io/description': 'for-test-update',
        'harvesterhci.io/host-custom-name': 'for-test-update'
    }
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


def test_update_using_yaml(request, admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    first_node = host_data['data'][0]
    first_node['metadata']['annotations'] = {
        'field.cattle.io/description': 'for-yaml-update',
        'harvesterhci.io/host-custom-name': 'for-yaml-update'
    }
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


@pytest.mark.delete_host
def test_delete_host(request, admin_session, harvester_api_endpoints):
    cur_endpoint = (request.config.getoption('--endpoint').split(":")[1])[2:]
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    for data in host_data['data']:
        if data['metadata']['annotations'].get(
                'etcd.k3s.cattle.io/node-address') != cur_endpoint:
            host_data_to_delete = data
    # delete the host
    utils.delete_host(request, admin_session, harvester_api_endpoints,
                      host_data_to_delete)
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    host_data = resp.json()
    assert host_data_to_delete not in host_data['data']


@pytest.mark.host_management
def test_host_mgmt_maintenance_mode(request, admin_session,
                                    harvester_api_endpoints):
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
    resp = admin_session.post(
        ret_data['actions']['disableMaintenanceMode'])
    assert resp.status_code == 204, (
        'Failed to update node: %s' % (resp.content))
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            ret_data["metadata"]["annotations"])


@pytest.mark.host_management
def test_host_reboot_maintenance_mode(request, admin_session,
                                      harvester_api_endpoints):
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
    resp = admin_session.post(
        ret_data['actions']['disableMaintenanceMode'])
    assert resp.status_code == 204, (
        'Failed to update node: %s' % (resp.content))
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"]
    assert ("harvesterhci.io/maintain-status" not in
            ret_data["metadata"]["annotations"])


@pytest.mark.host_management
def test_host_poweroff_state(request, admin_session,
                             harvester_api_endpoints):
    host_of = utils.lookup_host_not_harvester_endpoint(request, admin_session,
                                                       harvester_api_endpoints)
    # Power off Node
    node_name = host_of['id']
    utils.power_off_node(request, admin_session, harvester_api_endpoints,
                         node_name)
    resp = admin_session.get(
        harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert ret_data["metadata"]["state"]["name"] == "in-progress"
    # power On Node
    utils.power_on_node(request, admin_session, harvester_api_endpoints,
                        node_name)
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert ret_data["metadata"]["state"]["name"] == "active"
