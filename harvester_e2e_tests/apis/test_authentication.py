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

import requests
from urllib.parse import urljoin

pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.session'
  ]


# NOTE: include the admin_session here to ensure the password reset event
# has already occurred
def test_rancher_authentication(admin_session, request):
    username = request.config.getoption('--username')
    password = request.config.getoption('--password')
    rancher_endpoint = request.config.getoption('--endpoint')
    rancher_auth_url = urljoin(
            rancher_endpoint, '/v3-public/localProviders/local')
    login_data = {'username': username,
                  'password': password,
                  'responseType': 'json'}
    params = {'action': 'login'}
    resp = requests.post(
        rancher_auth_url, verify=False,
        params=params, json=login_data)
    assert resp.status_code in [200, 201], (
        'Unable to authenticate to Rancher')
    assert resp.json()['token'], 'Expecting token in the auth response: %s' % (
        resp.content)
