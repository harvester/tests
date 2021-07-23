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

import pytest


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.vm_template',
   'harvester_e2e_tests.fixtures.session',
  ]


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/968')
def test_verify_default_vm_templates(admin_session, harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_vm_templates)
    assert resp.status_code == 200, (
        'Failed to list virtual machine templates: %s' % (resp.content))
    vm_templates = resp.json()
    assert len(vm_templates['items']) == 3


def test_verify_default_vm_template_versions(admin_session,
                                             harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_vm_template_versions)
    assert resp.status_code == 200, (
        'Failed to list virtual machine template versions: %s' % (
            resp.content))
    vm_template_versions = resp.json()
    assert len(vm_template_versions['items']) == 3


@pytest.mark.skip(reason='https://github.com/harvester/harvester/issues/968')
def test_create_verify_vm_template(vm_template_version):
    # NOTE: if the vm_template_version fixture is successfully create that
    # means the test is successful.
    pass
