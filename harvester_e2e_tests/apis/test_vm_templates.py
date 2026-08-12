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

import re
from time import sleep
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
   "harvester_e2e_tests.fixtures.api_client"
  ]

# Default templates shipped in every supported version
BASE_TEMPLATES = {
    'iso-image-base-template',
    'raw-image-base-template',
    'windows-iso-image-base-template',
    'windows-raw-image-base-template',
}
# Size-tiered Windows templates added in v1.9.0
WINDOWS_TIERED_TEMPLATES = {
    'windows-iso-small-template',
    'windows-iso-medium-template',
    'windows-iso-large-template',
    'windows-w11-iso-template',
}
DEFAULT_TEMPLATES_NAMESPACE = 'harvester-public'


def _extract_release(text):
    """Extract a (major, minor, micro) tuple from a version-ish string."""
    match = re.search(r"v?(\d+)\.(\d+)(?:\.(\d+))?", text)
    if match:
        return tuple(int(g or 0) for g in match.groups())
    return None


def cluster_release(api_client):
    """Best-effort (major, minor, micro) of the cluster, None if unknown.

    Dev/CI builds carry a non-semver server-version (e.g.
    ``release-v1.9.0-rc5-b117-head``, ``v1.8-head`` or a commit hash), which
    breaks ``api_client.cluster_version`` parsing, so extract the release
    from the raw setting value instead. Versionless values (master/hash
    builds) yield None.
    """
    code, data = api_client.settings.get('server-version')
    return _extract_release(data.get('value', '') if code == 200 else '')


def expected_default_templates(api_client):
    """The exact default template set for the cluster's version.

    Versionless dev builds (master/commit-hash) are treated as the newest
    release.
    """
    release = cluster_release(api_client)
    if release and release < (1, 9, 0):
        return BASE_TEMPLATES
    return BASE_TEMPLATES | WINDOWS_TIERED_TEMPLATES


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.templates
@pytest.mark.negative
class TestVMTemplateNegative:
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.templates.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    def test_get_version_not_exist(self, api_client, unique_name):
        code, data = api_client.templates.get_version(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.templates.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get("reason"), (code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.templates
class TestVMTemplate:
    def test_create(self, api_client, unique_name):
        code, data = api_client.templates.create(unique_name)

        assert 201 == code, (code, data)
        assert unique_name == data['metadata']['name']

    @pytest.mark.dependency(name="get_template")
    def test_get(self, api_client, unique_name):
        # Case 1: get all templates
        code, data = api_client.templates.get()

        assert 200 == code, (code, data)
        assert len(data['items']) > 0, (code, data)

        # Case 2: get specific template by name
        code, data = api_client.templates.get(unique_name)

        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name']

    def test_update(self, api_client, unique_name):
        spec = api_client.templates.Spec(1, 2)

        code, data = api_client.templates.create_version(unique_name, spec)

        assert 201 == code, (code, data)
        assert data['metadata']['name'].startswith(unique_name), (code, data)

    def test_delete(self, api_client, unique_name, wait_timeout):
        code, data = api_client.templates.delete(unique_name)

        assert 200 == code, (f"Failed to delete template with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.templates.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete template {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    @pytest.mark.dependency(depends=["get_template"])
    def test_get_system_default(self, api_client):
        code, data = api_client.templates.get(namespace=DEFAULT_TEMPLATES_NAMESPACE)

        assert 200 == code, (code, data)
        names = {t['metadata']['name'] for t in data['items']}
        assert expected_default_templates(api_client) == names, (code, data)

    @pytest.mark.dependency(depends=["get_template"])
    def test_get_system_default_versions(self, api_client):
        code, tmpl_data = api_client.templates.get(namespace=DEFAULT_TEMPLATES_NAMESPACE)
        assert 200 == code, (code, tmpl_data)

        code, data = api_client.templates.get_version(namespace=DEFAULT_TEMPLATES_NAMESPACE)

        assert 200 == code, (code, data)
        names = {t['metadata']['name'] for t in tmpl_data['items']}
        version_template_ids = {v['spec']['templateId'].split('/')[-1] for v in data['items']}
        assert names == version_template_ids, (code, data)
