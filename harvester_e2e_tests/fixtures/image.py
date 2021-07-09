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
import polling2
import pytest
import time


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.api_version',
   'harvester_e2e_tests.fixtures.session',
  ]


def _delete_image(admin_session, harvester_api_endpoints, image_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_image % (
        image_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Unable to delete image %s: %s' % (
        image_json['metadata']['name'], resp.content)


def _create_image(request, admin_session, harvester_api_endpoints, url,
                  description=''):
    request_json = utils.get_json_object_from_template(
        'basic_image',
        description=description,
        url=url
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create image'
    image_json = resp.json()

    # wait for the image to get ready
    time.sleep(30)

    def _wait_for_image_become_active():
        # we want the update response to return back to the caller
        nonlocal image_json

        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to get image %s: %s' % (
            image_json['metadata']['name'], resp.content)
        image_json = resp.json()
        if ('status' in image_json and
                'storageClassName' in image_json['status']):
            return True
        return False

    success = polling2.poll(
        _wait_for_image_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be active.'

    return image_json


@pytest.fixture(scope='class')
def ubuntu_image(request, harvester_api_version, admin_session,
                 harvester_api_endpoints):
    url = ('http://cloud-images.ubuntu.com/releases/focal/release/'
           'ubuntu-20.04-server-cloudimg-amd64-disk-kvm.img')
    image_json = _create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='Ubuntu 20.04 Server')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        _delete_image(admin_session, harvester_api_endpoints, image_json)


@pytest.fixture(scope='class')
def k3os_image(request, harvester_api_version, admin_session,
               harvester_api_endpoints):
    url = ('https://github.com/rancher/k3os/releases/download/v0.20.4-k3s1r0/'
           'k3os-amd64.iso')
    image_json = _create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='K3OS')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        _delete_image(admin_session, harvester_api_endpoints, image_json)


@pytest.fixture(scope='class')
def opensuse_image(request, harvester_api_version, admin_session,
                   harvester_api_endpoints):
    url = ('https://download.opensuse.org/tumbleweed/iso/'
           'openSUSE-Tumbleweed-NET-x86_64-Current.iso')
    image_json = _create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='openSUSE Tumbleweed')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        _delete_image(admin_session, harvester_api_endpoints, image_json)


@pytest.fixture(scope='class')
def image(request, admin_session, harvester_api_endpoints):
    url = ('http://download.opensuse.org/repositories/Cloud:/Images:/'
           'Leap_15.2/images/openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')

    # when use parameterized fixture, use the URL from the parameter instead
    if getattr(request, 'param', None):
        url = request.param

    image_json = _create_image(request, admin_session, harvester_api_endpoints,
                               url)
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        _delete_image(admin_session, harvester_api_endpoints, image_json)
