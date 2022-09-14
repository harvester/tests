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
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.api_client'
]


@pytest.mark.p1
@pytest.mark.negative
@pytest.mark.volumes
class TestVolumesNegative:
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.volumes.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.volumes.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get("reason"), (code, data)

    def test_create_without_size(self, api_client, unique_name):
        code, data = api_client.volumes.create(unique_name, 0)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("reason"), (code, data)

    def test_create_without_name(self, api_client):
        code, data = api_client.volumes.create("", 1)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("reason"), (code, data)


@pytest.mark.p1
@pytest.mark.volumes
class TestVolumes:
    def test_create(self, api_client, unique_name):
        code, data = api_client.volumes.create(unique_name, 1)

        assert 201 == code, (code, data)

    def test_get(self, api_client, unique_name):
        # Case 1: get all volumes
        code, data = api_client.volumes.get()

        assert 200 == code, (code, data)
        assert len(data['items']) > 0, (code, data)

        # Case 2: get specific volume
        code, data = api_client.volumes.get(unique_name)

        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name'], (code, data)

    def test_update_size(self, api_client, unique_name, wait_timeout):
        # Pre-condition: Volume is Ready
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(unique_name)
            if "Bound" == data['status']['phase']:
                break
            sleep(5)
        else:
            raise AssertionError(
                "Volume not changed to phase: _Bound_ with {wait_timeout} timed out\n"
                f"Got error: {code}, {data}"
            )

        updates = {
            "spec": {
                "resources": {
                    "requests": {
                        "storage": "10Gi"
                    }
                }
            }
        }
        code, data = api_client.volumes.update(unique_name, updates)

        assert 200 == code, (f"Failed to update volume with error: {code}, {data}")

    def test_delete(self, api_client, unique_name, wait_timeout):
        code, data = api_client.volumes.delete(unique_name)

        assert 200 == code, (f"Failed to delete volume with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete volume {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )
