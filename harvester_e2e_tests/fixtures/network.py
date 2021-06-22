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
   'harvester_e2e_tests.fixtures.api_version',
   'harvester_e2e_tests.fixtures.session',
  ]


@pytest.fixture(scope='class')
def network(request, kubevirt_api_version, admin_session,
            harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_network'
    )
    resp = admin_session.post(harvester_api_endpoints.create_network,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a network: %s' % (
        resp.content)
    network_data = resp.json()
    utils.poll_for_resource_ready(admin_session, network_data['links']['view'])
    yield network_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_network % (
                network_data['id']))
        assert resp.status_code in [200, 204], (
            'Unable to cleanup network: %s' % (resp.content))
