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


@pytest.fixture(scope='session')
def admin_session(request, harvester_api_endpoints):
    username = request.config.getoption('--username')
    password = request.config.getoption('--password')

    # authenticate admin
    login_data = {'username': username, 'password': password}
    params = {'action': 'login'}
    s = utils.retry_session()
    resp = s.post(harvester_api_endpoints.local_auth,
                  params=params, json=login_data)
    assert resp.status_code == 201, 'Failed to authenticate admin user: %s' % (
        resp.content)
    auth_token = 'Bearer ' + resp.json()['token']
    s.headers.update({'Authorization': auth_token})
    return s


@pytest.fixture(scope='session')
def harvester_cluster_nodes(request):
    nodes = request.config.getoption('--harvester_cluster_nodes')
    return nodes


@pytest.fixture(scope='session')
def rancher_admin_session(request, rancher_api_endpoints):
    password = request.config.getoption('--rancher-admin-password')

    # authenticate admin
    login_data = {'username': 'admin', 'password': password,
                  'responseType': 'json'}
    params = {'action': 'login'}
    s = utils.retry_session()
    resp = s.post(rancher_api_endpoints.local_auth,
                  params=params, json=login_data)
    assert resp.status_code == 201, (
        'Failed to authenticate admin user: %s' % (resp.content))
    auth_token = 'Bearer ' + resp.json()['token']
    s.headers.update({'Authorization': auth_token})
    return s
