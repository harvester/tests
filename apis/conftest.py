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
import urllib.parse
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def pytest_addoption(parser):
    parser.addoption(
        '--endpoint',
        action='store',
        default='https://localhost:8443',
        help='Harvester API endpoint'
    )
    parser.addoption(
        '--username',
        action='store',
        default='admin',
        help='Harvester username'
    )
    parser.addoption(
        '--password',
        action='store',
        default='password',
        help='Harvester password'
    )
    parser.addoption(
        '--set_admin_password',
        action='store_true',
        help='Set admin password on the first login.'
    )
    parser.addoption(
        '--harvester_cluster_nodes',
        action='store',
        type='int',
        help='Set count of test framework harvester cluster nodes.'
    )
    # TODO(gyee): may need to add SSL options later


def _set_admin_password(endpoint, password):
    login_data = {'username': 'admin', 'password': 'admin',
                  'responseType': 'json'}
    params = {'action': 'login'}
    k3os_auth_endpoint = urllib.parse.urljoin(
        endpoint, '/v3-public/localProviders/local')
    resp = requests.post(
        k3os_auth_endpoint, verify=False, params=params, json=login_data)
    bearer_token = 'Bearer ' + resp.json()['token']

    reset_password_data = {'currentPassword': 'admin',
                           'newPassword': password}
    reset_password_endpoint = urllib.parse.urljoin(
        endpoint, '/v3/users')
    params = {'action': 'changepassword'}
    headers = {'authorization': bearer_token}
    resp = requests.post(
        reset_password_endpoint, verify=False, headers=headers,
        params=params, json=reset_password_data)


@pytest.fixture(scope='session')
def harvester_auth_session(request):
    endpoint = request.config.getoption('--endpoint')
    username = request.config.getoption('--username')
    password = request.config.getoption('--password')
    set_admin_password = request.config.getoption('--set_admin_password')
    harvester_cluster_nodes = request.config.getoption('--harvester_cluster_nodes')

    if set_admin_password:
        _set_admin_password(endpoint, password)

    # FIXME(gyee): this is just a temporary hack to get around
    # https://github.com/harvester/harvester/issues/893
    # First we need to reset password for admin

    login_data = {'username': username, 'password': password}
    params = {'action': 'login'}
    s = requests.Session()
    # TODO(gyee): do we need to support other auth methods?
    auth_endpoint = urllib.parse.urljoin(
        endpoint, '/v3-public/localProviders/local')
    # NOTE(gyee): ignore SSL certificate validation for now
    resp = s.post(auth_endpoint, verify=False, params=params, json=login_data)
    s.headers.update({'Authorization': 'Bearer ' + resp.json()['token']})
    return s


@pytest.fixture(scope='session')
def harvester_endpoint(request):
    return request.config.getoption('--endpoint')

@pytest.fixture(scope='session')
def harvester_cluster_nodes(request):
    return request.config.getoption('--harvester_cluster_nodes')
