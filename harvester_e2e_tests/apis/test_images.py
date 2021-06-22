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
   'harvester_e2e_tests.fixtures.image',
   'harvester_e2e_tests.fixtures.keypair',
   'harvester_e2e_tests.fixtures.volume',
  ]


def test_list_images(admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_images)
    assert resp.status_code == 200, (
        'Failed to list images: %s' % (resp.content))


def test_create_image_no_data(admin_session, harvester_api_endpoints):
    no_image_data = {
        'apiVersion': 'harvesterhci.io/v1beta1',
        'kind': 'VirtualMachineImage'
    }
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=no_image_data)
    assert resp.status_code == 422, (
        'Expecting 422 when creating image with invalid image request')
    response_data = resp.json()
    assert 'name or generateName is required' in response_data['message']


def test_create_image_no_url(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template(
        'basic_image',
        description='Leap 15.2 cloud image',
        url=''
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code == 201, 'Failed to create image: %s' % (
        resp.content)
    image_data = resp.json()
    resp = admin_session.delete(harvester_api_endpoints.delete_image % (
        image_data['metadata']['name']))
    assert resp.status_code == 200, 'Unable to delete image: %s' % (
        resp.content)


def test_create_images(admin_session, image):
    # NOTE: the image fixture will be creating the image and check the result
    pass


def test_update_images(admin_session, harvester_api_endpoints, image):
    image['metadata']['labels'] = {
        'test.harvesterhci.io': 'for-test-update'
    }
    image['metadata']['annotations'] = {
        'test.harvesterhci.io': 'for-test-update'
    }
    resp = admin_session.put(harvester_api_endpoints.update_image % (
        image['metadata']['name']), json=image)
    assert resp.status_code == 200, 'Failed to update image: %s' % (
        resp.content)
    update_image_data = resp.json()
    assert update_image_data['metadata']['labels'] == {
        'test.harvesterhci.io': 'for-test-update'
    }
    assert update_image_data['metadata']['annotations'] == {
        'test.harvesterhci.io': 'for-test-update'
    }
