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
import bcrypt


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.user',
   'harvester_e2e_tests.fixtures.session',
  ]


def test_create_users(user):
    # user creation is tested implicitly by successfully creating
    # the user fixture
    pass


def test_get_user(admin_session, user):
    resp = admin_session.get(user['links']['view'])
    assert resp.status_code == 200, 'Failed to get user: %s' % (resp.content)
    ret_user_data = resp.json()
    assert ret_user_data['displayName'] == user['displayName']
    assert ret_user_data['description'] == user['description']
    assert ret_user_data['username'] == user['username']


def test_update_user_password(admin_session, user):
    request_json = utils.get_json_object_from_template(
        'basic_user', password='UpdatedTestF00Bar')
    request_json['username'] = user['username']
    request_json['displayName'] = user['displayName']
    del request_json['description']
    del request_json['isAdmin']
    request_json['metadata'] = {'name': user['metadata']['name']}
    resp = utils.poll_for_update_resource(
        admin_session,
        user['links']['update'],
        request_json,
        user['links']['view'])
    get_updated_user = resp.json()
    updatedPassStr = str.encode('UpdatedTestF00Bar')
    assert bcrypt.checkpw(
        updatedPassStr, get_updated_user['password'].encode('utf-8'))
