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
def vm_template(request, kubevirt_api_version, admin_session,
                harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_vm_template')
    resp = admin_session.post(harvester_api_endpoints.create_vm_template,
                              json=request_json)
    assert resp.status_code == 201, (
        'Unable to create virtual machine template: %s' % (resp.content))
    vm_template_data = resp.json()
    yield vm_template_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_vm_template % (
                vm_template_data['metadata']['name']))
        assert resp.status_code == 200, (
            'Unable to cleanup virtual machine template: %s' % (resp.content))


@pytest.fixture(scope='class')
def vm_template_version(request, kubevirt_api_version, admin_session,
                        harvester_api_endpoints, vm_template):
    request_json = utils.get_json_object_from_template(
        'basic_vm_template_version',
        name=vm_template['metadata']['name'])
    resp = admin_session.post(
        harvester_api_endpoints.create_vm_template_version,
        json=request_json)
    assert resp.status_code == 201, (
        'Unable to create virtual machine template version: %s' % (
            resp.content))
    vm_template_version_data = resp.json()
    yield vm_template_version_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_vm_template_version % (
                vm_template_version_data['metadata']['name']))
        assert resp.status_code == 200, (
            'Unable to cleanup virtual machine template version: %s' % (
                resp.content))
