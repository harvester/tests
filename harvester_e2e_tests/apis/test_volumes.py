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
from time import sleep
import yaml


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.volume',
   'harvester_e2e_tests.fixtures.session',
  ]


def test_create_volume_missing_size(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    del request_json['spec']['pvc']['resources']['requests']['storage']
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when attempting to create volume without '
        'specifying storage size: %s' % (resp.content))
    response_data = resp.json()
    assert 'PVC size is missing' in response_data['message']


def test_create_volume_missing_name(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    del request_json['metadata']['name']
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when attempting to create volume without '
        'specifying a name: %s' % (resp.content))
    response_data = resp.json()
    assert 'name or generateName is required' in response_data['message']


def test_create_volumes(volume):
    # NOTE: if the volume is successfully create that means the test is good
    pass


def test_create_volume_by_yaml(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              data=yaml.dump(request_json, sort_keys=False),
                              headers={'Content-Type': 'application/yaml'})
    assert resp.status_code == 201, (
        'Failed to create volume with YAML request: %s' % (resp.content))
    view_endpoint = harvester_api_endpoints.get_volume % (
        request_json['metadata']['name'])
    assert validate_blank_volumes(admin_session, view_endpoint)
    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        request_json['metadata']['name']))
    # FIXME(gyee): we need to figure out why the API can arbitarily return
    # 200 or 204. It should consistently returning one.
    assert resp.status_code in [200, 204], 'Failed to delete volume: %s' % (
        resp.content)


def validate_blank_volumes(admin_session, get_api_link):
    for x in range(10):
        resp = admin_session.get(get_api_link)
        assert resp.status_code == 200, 'Failed to get volume: %s' % (
            resp.content)
        ret_data = resp.json()
        sleep(5)
        if 'status' in ret_data and ret_data['status']['phase'] == 'Succeeded':
            return True
    return False
