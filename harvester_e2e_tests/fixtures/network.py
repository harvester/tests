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


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.session',
  ]


@pytest.fixture(scope='session')
def enable_vlan(request, admin_session, harvester_api_endpoints):
    vlan_nic = request.config.getoption('--vlan-nic')
    resp = admin_session.get(harvester_api_endpoints.get_vlan)
    assert resp.status_code == 200, 'Failed to get vlan: %s' % (resp.content)
    vlan_json = resp.json()
    if 'config' not in vlan_json:
        vlan_json['config'] = {}
    if 'defaultPhysicalNIC' not in vlan_json['config']:
        vlan_json['config']['defaultPhysicalNIC'] = None
    vlan_json['enable'] = True
    vlan_json['config']['defaultPhysicalNIC'] = vlan_nic
    utils.poll_for_update_resource(request, admin_session,
                                   harvester_api_endpoints.update_vlan,
                                   vlan_json,
                                   harvester_api_endpoints.get_vlan)


def _cleanup_network(admin_session, harvester_api_endpoints, network_id,
                     wait_timeout):

    def _delete_network():
        resp = admin_session.delete(
            harvester_api_endpoints.delete_network % (network_id))
        if resp.status_code in [200, 204]:
            return True
        elif resp.status_code == 400:
            return False
        else:
            assert False, 'Failed to cleanup network %s: %s' % (
                network_id, resp.content)

    # NOTE(gyee): there's no way we know how many VMs the network is currently
    # attached to. Will need to keep trying till all the VMs had been deleted
    success = polling2.poll(
        _delete_network,
        step=5,
        timeout=wait_timeout)
    assert success, 'Unable to cleanup network: %s' % (network_id)


def _create_network(request, admin_session, harvester_api_endpoints, vlan_id):
    request_json = utils.get_json_object_from_template(
        'basic_network',
        vlan=vlan_id
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a network: %s' % (
        resp.content)
    network_data = resp.json()
    utils.poll_for_resource_ready(request, admin_session,
                                  network_data['links']['view'])
    return network_data


@pytest.fixture(scope='session')
def network(request, admin_session, harvester_api_endpoints, enable_vlan):
    vlan_id = request.config.getoption('--vlan-id')
    # don't create network if VLAN is not correctly specified
    if vlan_id == -1:
        return

    network_data = _create_network(request, admin_session,
                                   harvester_api_endpoints, vlan_id)
    yield network_data

    if not request.config.getoption('--do-not-cleanup'):
        _cleanup_network(admin_session, harvester_api_endpoints,
                         network_data['id'],
                         request.config.getoption('--wait-timeout'))


@pytest.fixture(scope='class')
def bogus_network(request, admin_session, harvester_api_endpoints,
                  enable_vlan):
    vlan_id = request.config.getoption('--vlan-id')
    # don't create network if VLAN is not correctly specified
    if vlan_id == -1:
        return
    # change the VLAN ID to an invalid one
    vlan_id += 1

    network_data = _create_network(request, admin_session,
                                   harvester_api_endpoints, vlan_id)
    yield network_data

    if not request.config.getoption('--do-not-cleanup'):
        _cleanup_network(admin_session, harvester_api_endpoints,
                         network_data['id'],
                         request.config.getoption('--wait-timeout'))


# This fixture is only called by test_create_edit_network
# in apis/test_networks.py.
# vlan_id is set to vlan_id + 1
@pytest.fixture(scope='class')
def network_for_update_test(request, admin_session,
                            harvester_api_endpoints, enable_vlan):
    vlan_id = request.config.getoption('--vlan-id')
    # don't create network if VLAN is not correctly specified
    if vlan_id == -1:
        return

    request_json = utils.get_json_object_from_template(
        'basic_network',
        vlan=vlan_id + 1
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a network: %s' % (
        resp.content)
    network_data = resp.json()
    utils.poll_for_resource_ready(request, admin_session,
                                  network_data['links']['view'])
    yield network_data

    if not request.config.getoption('--do-not-cleanup'):
        _cleanup_network(admin_session, harvester_api_endpoints,
                         network_data['id'],
                         request.config.getoption('--wait-timeout'))
