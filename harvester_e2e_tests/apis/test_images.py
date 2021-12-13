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
import os
import polling2
import pytest

pytest_plugins = [
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.keypair',
    'harvester_e2e_tests.fixtures.volume',
]


def test_list_images(admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_images)
    assert resp.status_code == 200, (
        'Failed to list images: %s' % (resp.content))


@pytest.mark.images_p2
@pytest.mark.p2
def test_create_image_no_data(admin_session, harvester_api_endpoints):
    """
    Test creating image with no data

    Covers:
        Negative test images-3-Create Image no data
    """
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


@pytest.mark.images_p2
@pytest.mark.p2
def test_create_image_no_url(admin_session, harvester_api_endpoints):
    """
    Test creating image with no url

    Covers:
        Negative test images-3-Create Image no data
    """
    request_json = utils.get_json_object_from_template(
        'basic_image',
        description='Leap 15.2 cloud image',
        url=''
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expecting HTTP 422 for attempting to create an image with an empty '
        'URL %s:%s ' % (resp.status_code, resp.content))


@pytest.mark.images_p1
@pytest.mark.p1
def test_create_image_with_reuse_display_name(request, admin_session,
                                              harvester_api_endpoints):
    """
    Test Delete image

    Covers:
        images-6-Delete Image
    """
    name = utils.random_name()
    base_url = request.config.getoption(
        '--image-cache-url',
        ('http://download.opensuse.org/repositories/Cloud:/Images:/'
         'Leap_15.2/images'))
    url = os.path.join(base_url, 'openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')
    # create the image
    image_json = utils.create_image(request, admin_session,
                                    harvester_api_endpoints, url,
                                    name=name,
                                    description='Leap 15.2 cloud image')
    old_image_name = image_json['metadata']['name']
    # delete the image
    utils.delete_image(request, admin_session, harvester_api_endpoints,
                       image_json)
    # create a different image with the same display name and it should be
    # allowed
    image_json = utils.create_image(request, admin_session,
                                    harvester_api_endpoints, url,
                                    name=name,
                                    description='Leap 15.2 cloud image')
    # delete the image
    utils.delete_image(request, admin_session, harvester_api_endpoints,
                       image_json)
    # the names should be the same
    assert image_json['metadata']['name'] == old_image_name, (
        'Expecting new image to have the same name')
    assert image_json['spec']['displayName'] == name, (
        'Expecting new image to have the same display name')


@pytest.mark.images_p2
@pytest.mark.p2
@pytest.mark.parametrize('image', ['https://test_bogus.img'], indirect=True)
def test_create_image_with_invalid_url(request, admin_session,
                                       harvester_api_endpoints, image):
    """
    Test Invalid image

    Covers:
        images-2-Invalid Image
    """
    image_json = None

    def _check_image_status():
        nonlocal image_json
        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image['metadata']['name']))
        assert resp.status_code == 200, 'Failed to lookup image %s: %s' % (
            image['metadata']['name'], resp.content)
        image_json = resp.json()
        if ('status' in image_json and 'conditions' in image_json['status'] and
                len(image_json['status']['conditions']) == 1 and
                'status' in image_json['status']['conditions'][0]):
            return True
        return False

    success = polling2.poll(
        _check_image_status,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image status'
    image_status = image_json['status']['conditions'][0]['status'].lower()
    assert image_status == 'false', (
        'Expecting image creation to fail on bogus URL')


@pytest.mark.images_p1
@pytest.mark.p1
def test_create_images(admin_session, image):
    """
    Test Create image

    Covers:
        images-1-Create Image
    """
    # NOTE: the image fixture will be creating the image and check the result
    pass


@pytest.mark.images_p1
@pytest.mark.p1
@pytest.mark.imageupload
def test_image_upload(request, admin_session, image_upload_fs, keypair,
                      harvester_api_endpoints):
    """
    Test create upload image

    Covers:
        images-7-Upload Image, only check Image is active (does not create vm)
    """
    # NOTE: the image fixture will be uploading the image and check the result
    pass


@pytest.mark.images_p1
@pytest.mark.p1
def test_update_images(admin_session, harvester_api_endpoints, image):
    """
    Test Edit Image and Add Labels

    Covers:
        images-3-Edit Image and images-4-Add Labels
    """
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


@pytest.mark.terraform_provider_p1
@pytest.mark.p1
# This test covers terraform-5-Harvester image as a pre-req it covers
# terraform-1-install, terraform-2-kube config, terraform-3-define kube config
@pytest.mark.terraform
def test_create_images_using_terraform(admin_session, image_using_terraform):
    """
    Test creates Harvester Image

    Covers:
        terraform-provider-05-Harvester image as a pre-req it covers
        terraform-provider-01-install, terraform-provider-02-kube config,
        terraform-provider-03-define
        kube config
    """
    # NOTE: the image fixture will be creating the image and check the result
    pass
