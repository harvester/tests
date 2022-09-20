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

from time import sleep
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
   "harvester_e2e_tests.fixtures.api_client"
  ]

DEFAULT_TEMPLATES = 4
DEFAULT_TEMPLATES_NAMESPACE = 'harvester-public'


@pytest.mark.p1
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


@pytest.mark.p1
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
        config = {
            "cpu": 1,
            "memory": "2Gi",
        }
        code, data = api_client.templates.update(unique_name, **config)

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
        assert DEFAULT_TEMPLATES == len(data['items']), (code, data)

    @pytest.mark.dependency(depends=["get_template"])
    def test_get_system_default_versions(self, api_client):
        code, data = api_client.templates.get_version(namespace=DEFAULT_TEMPLATES_NAMESPACE)

        assert 200 == code, (code, data)
        assert DEFAULT_TEMPLATES == len(data['items']), (code, data)
