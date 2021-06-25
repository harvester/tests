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


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.session',
  ]


def test_list_settingss(admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_harvester_settings)
    assert resp.status_code == 200, 'Failed to list Harvester settings: %s' % (
        resp.content)


def test_update_api_ui_version(admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.get_api_ui_version)
    assert resp.status_code == 200, (
        'Failed to get Harvester API UI version: %s' % (resp.content))
    api_ui_version_data = resp.json()
    request_json = utils.get_json_object_from_template(
        'api_ui_version_setting')
    resp = utils.poll_for_update_resource(
        admin_session,
        api_ui_version_data['links']['update'],
        request_json,
        harvester_api_endpoints.get_api_ui_version)
    updated_settings_data = resp.json()
    assert updated_settings_data['value'] == request_json['value'], (
        'Failed to update API UI version')
    # now change it back
    request_json['value'] = api_ui_version_data['value']
    utils.poll_for_update_resource(
        admin_session,
        updated_settings_data['links']['update'],
        request_json,
        harvester_api_endpoints.get_api_ui_version)
