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
def ubuntu_image(request, harvester_api_version, admin_session,
                 harvester_api_endpoints):
    url = ('http://cloud-images.ubuntu.com/releases/focal/release/'
           'ubuntu-20.04-server-cloudimg-amd64-disk-kvm.img')
    image_json = utils.create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='Ubuntu 20.04 Server')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_image(request, admin_session, harvester_api_endpoints,
                           image_json)


@pytest.fixture(scope='class')
def windows_image(request, harvester_api_version, admin_session,
                  harvester_api_endpoints):
    url = request.config.getoption('--win-image-url')
    image_json = None
    if url != '':
        image_json = utils.create_image(
            request, admin_session, harvester_api_endpoints, url,
            description='Windows 2016')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        if image_json:
            utils.delete_image(request, admin_session, harvester_api_endpoints,
                               image_json)


@pytest.fixture(scope='class')
def k3os_image(request, harvester_api_version, admin_session,
               harvester_api_endpoints):
    url = ('https://github.com/rancher/k3os/releases/download/v0.20.4-k3s1r0/'
           'k3os-amd64.iso')
    image_json = utils.create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='K3OS')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_image(request, admin_session, harvester_api_endpoints,
                           image_json)


@pytest.fixture(scope='class')
def opensuse_image(request, harvester_api_version, admin_session,
                   harvester_api_endpoints):
    url = ('https://download.opensuse.org/tumbleweed/iso/'
           'openSUSE-Tumbleweed-NET-x86_64-Current.iso')
    image_json = utils.create_image(
        request, admin_session, harvester_api_endpoints, url,
        description='openSUSE Tumbleweed')
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_image(request, admin_session, harvester_api_endpoints,
                           image_json)


@pytest.fixture(scope='class')
def image(request, admin_session, harvester_api_endpoints):
    url = ('http://download.opensuse.org/repositories/Cloud:/Images:/'
           'Leap_15.2/images/openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')

    # when use parameterized fixture, use the URL from the parameter instead
    if getattr(request, 'param', None):
        url = request.param

    image_json = utils.create_image(request, admin_session,
                                    harvester_api_endpoints, url)
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        utils.delete_image(request, admin_session, harvester_api_endpoints,
                           image_json)


@pytest.fixture(scope='class')
def image_using_terraform(request, admin_session, harvester_api_endpoints):
    url = ('http://download.opensuse.org/repositories/Cloud:/Images:/'
           'Leap_15.2/images/openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')

    # when use parameterized fixture, use the URL from the parameter instead
    if getattr(request, 'param', None):
        url = request.param

    image_json = utils.create_image_terraform(request, admin_session,
                                              harvester_api_endpoints, url)
    yield image_json
    if not request.config.getoption('--do-not-cleanup'):
        print("Destroy resource")
        utils.destroy_resource(request, admin_session, 'None')
        utils.delete_image(request, admin_session, harvester_api_endpoints,
                           image_json, use_terraform=True)
