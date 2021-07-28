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
import requests


def _set_admin_password(harvester_api_endpoints, password):
    # first obtain the token using the default admin password
    login_data = {'username': 'admin', 'password': 'admin',
                  'responseType': 'json'}
    params = {'action': 'login'}
    resp = requests.post(
        harvester_api_endpoints.local_auth, verify=False,
        params=params, json=login_data)
    # FIXME(gyee): it seems like Harvester API is returning a different status
    # code in different releases even though the API version hasn't changed.
    # For now, lets account for both 200 and 201 as valid error codes.
    assert resp.status_code in [200, 201], (
        'Unable to authenticate admin with default password')

    # now reset the admin password
    bearer_token = 'Bearer ' + resp.json()['token']
    headers = {'authorization': bearer_token}

    reset_password_data = {'currentPassword': 'admin',
                           'newPassword': password}
    params = {'action': 'changepassword'}
    resp = requests.post(
        harvester_api_endpoints.reset_password, verify=False, headers=headers,
        params=params, json=reset_password_data)
    assert resp.status_code == 200, 'Unable to reset admin password'


@pytest.fixture(scope='session')
def admin_session(request, harvester_api_endpoints):
    username = request.config.getoption('--username')
    password = request.config.getoption('--password')

    # set admin password if needed
    _set_admin_password(harvester_api_endpoints, password)

    # authenticate admin
    login_data = {'username': username, 'password': password}
    params = {'action': 'login'}
    s = requests.Session()
    # TODO(gyee): do we need to support other auth methods?
    # NOTE(gyee): ignore SSL certificate validation for now
    resp = s.post(harvester_api_endpoints.local_auth, verify=False,
                  params=params, json=login_data)
    auth_token = 'Bearer ' + resp.json()['token']
    s.headers.update({'Authorization': auth_token})
    return s


@pytest.fixture(scope='session')
def harvester_cluster_nodes(request):
    nodes = request.config.getoption('--harvester_cluster_nodes')
    return nodes
