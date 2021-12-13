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
import json
import pytest


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.network',
   'harvester_e2e_tests.fixtures.session',
  ]


def test_create_with_vid_0(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_network',
        vlan=0
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 422, ('Expected HTTP 422 when trying to create '
                                     'network with vlan ID 0')
    response_data = resp.json()
    assert 'must >=1' in response_data['message']


def test_create_with_vid_4095(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_network',
        vlan=4095
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when trying to create network with vlan ID 4095')
    response_data = resp.json()
    assert 'and <=4094' in response_data['message']


@pytest.mark.network_p2
@pytest.mark.p2
def test_create_network_with_no_name(admin_session, harvester_api_endpoints):
    """
    Negative test to create network with no name
    Covers:
        network-03-Test create network with no name
    """
    request_json = utils.get_json_object_from_template(
        'basic_network',
        vlan=4000,
        name=''
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when trying to create network with no name')
    response_data = resp.json()
    assert 'name or generateName is required' in response_data['message']


@pytest.mark.public_network
def test_create_edit_network(request, admin_session, harvester_api_endpoints,
                             network_for_update_test):
    request_json = utils.get_json_object_from_template(
        'basic_network'
    )
    conf_data = json.loads(network_for_update_test['spec']['config'])
    # network_for_update_test fixture creates vlan with vlan_id +1.
    # Here update with -1.
    updated_vlan = conf_data['vlan'] - 1
    conf_data['vlan'] = updated_vlan
    request_json['spec']['config'] = json.dumps(conf_data)
    request_json['metadata']['name'] = \
        network_for_update_test['metadata']['name']
    request_json['metadata']['namespace'] = \
        network_for_update_test['metadata']['namespace']
    resp = utils.poll_for_update_resource(
        request, admin_session,
        network_for_update_test['links']['update'],
        request_json,
        network_for_update_test['links']['view'])
    updated_network_data = resp.json()
    updated_config = json.loads(updated_network_data['spec']['config'])
    assert updated_config['vlan'] == updated_vlan, 'Failed to update vlan'


@pytest.mark.terraform_provider_p1
@pytest.mark.p1
@pytest.mark.terraform
@pytest.mark.public_network
def test_create_network_using_terraform(request, admin_session,
                                        harvester_api_endpoints,
                                        network_using_terraform):
    """
    Test creates Terraform Harvester
    Covers:
        terraform-provider-06-Harvester network as a pre-req it covers
        terraform-provider-08-Harvester cluster network during enable vlan
        terraform-provider-01-install, terraform-provider-02-kube config,
        terraform-provider-03-define
        kube config
    """
    pass
