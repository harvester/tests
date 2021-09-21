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

import yaml
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.session',
]


def test_create_keypair_missing_name(admin_session, harvester_api_endpoints,
                                     keypair_request_json):
    keypair_request_json[0]['metadata']['name'] = ''
    resp = admin_session.post(harvester_api_endpoints.create_keypair,
                              json=keypair_request_json[0])
    assert resp.status_code == 422, 'Expected 422 if keypair name is empty'
    response_data = resp.json()
    assert 'name or generateName is required' in response_data['message']


def test_create_keypair_missing_key(admin_session, harvester_api_endpoints,
                                    keypair_request_json):
    keypair_request_json[0]['spec']['publicKey'] = ''
    resp = admin_session.post(harvester_api_endpoints.create_keypair,
                              json=keypair_request_json[0])
    assert resp.status_code == 422, 'Expected 422 if publicKey is empty'
    response_data = resp.json()
    assert 'public key is required' in response_data['message']


def test_create_keypair_invalid_key(admin_session, harvester_api_endpoints,
                                    keypair_request_json):
    keypair_request_json[0]['spec']['publicKey'] = 'invalid test public key'
    resp = admin_session.post(harvester_api_endpoints.create_keypair,
                              json=keypair_request_json[0])
    assert resp.status_code == 422, 'Expected 422 if publicKey is empty'
    response_data = resp.json()
    assert ('key is not in valid OpenSSH public key format' in
            response_data['message'])


def test_create_keypairs(keypair):
    # keypair creation validation is done in the fixture already
    pass


def test_create_keypair_by_yaml(admin_session, harvester_api_endpoints,
                                keypair_request_json):
    resp = admin_session.post(
        harvester_api_endpoints.create_keypair,
        data=yaml.dump(keypair_request_json[0], sort_keys=False),
        headers={'Content-Type': 'application/yaml'})
    assert resp.status_code == 201, 'Failed to create keypair: %s' % (
        resp.content)
    keypair_data = resp.json()
    resp = admin_session.delete(harvester_api_endpoints.delete_keypair % (
        keypair_data['metadata']['name']))
    assert resp.status_code == 200, 'Failed to delete keypair: %s' % (
        resp.content)


@pytest.mark.terraform_1
def test_create_keypairs_using_terraform(keypair_using_terraform):
    # keypair creation validation is done in the fixture already
    pass
