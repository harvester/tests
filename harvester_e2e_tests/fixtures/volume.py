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
def volume(request, kubevirt_api_version, admin_session,
           harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_volume',
        size=8,
        description='Test volume'
    )
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a blank volume'
    volume_data = resp.json()
    yield volume_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_volume % (
                volume_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup volume'


@pytest.fixture(scope='class')
def volume_image_form(request, kubevirt_api_version, admin_session,
                      harvester_api_endpoints, image):
    request_json = utils.get_json_object_from_template(
        'basic_volume',
        size=8,
        description='Test volume using Image Form'
    )
    imageid = "/".join([image['metadata']['namespace'],
                       image['metadata']['name']])
    request_json['metadata']['annotations'][
        'harvesterhci.io/imageId'] = imageid
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a blank volume'
    volume_data = resp.json()
    assert volume_data['metadata']['annotations'].get(
        'harvesterhci.io/imageId') == imageid
    yield volume_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_volume % (
                volume_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup volume'


@pytest.fixture(scope='class')
def volume_with_image(request, kubevirt_api_version, admin_session,
                      harvester_api_endpoints, image):
    request_json = utils.get_json_object_from_template(
        'basic_volume',
        size=8,
        description='Test volume using Image & Label'
    )
    imageid = "/".join([image['metadata']['namespace'],
                       image['metadata']['name']])
    request_json['metadata']['annotations'][
        'harvesterhci.io/imageId'] = imageid
    request_json['metadata']['labels'] = {
        'test.harvesterhci.io': 'for-test'
    }
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create a blank volume'
    volume_data = resp.json()
    assert volume_data['metadata']['annotations'].get(
        'harvesterhci.io/imageId') == imageid
    assert volume_data['metadata']['labels'].get(
        'test.harvesterhci.io') == 'for-test'
    yield volume_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_volume % (
                volume_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup volume'
