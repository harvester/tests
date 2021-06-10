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

from scenarios import utils
import pytest


pytest_plugins = [
   'scenarios.fixtures.api_endpoints',
   'scenarios.fixtures.api_version',
   'scenarios.fixtures.session',
  ]


@pytest.fixture(scope='class')
def image(request, harvester_api_version, admin_session,
          harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_image',
        description='Leap 15.2 cloud image',
        url=('http://download.opensuse.org/repositories/Cloud:/Images:/'
             'Leap_15.2/images/openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create image'
    image_data = resp.json()
    yield image_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_image % (
                image_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup image'
