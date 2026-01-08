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

VLAN_ID = 4000


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.negative
@pytest.mark.networks
class TestNetworksNegative:

    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.networks.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.networks.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get("reason"), (code, data)

    @pytest.mark.parametrize("vlan_id", [0, 4095])
    @pytest.mark.skip_if_version(
            ">= v1.0.3", reason="https://github.com/harvester/harvester/issues/3151")
    def test_create_with_invalid_id_103(self, api_client, unique_name, vlan_id):
        code, data = api_client.networks.create(unique_name, vlan_id)

        assert 422 == code, (vlan_id, code, data)
        assert "Invalid" == data.get("reason"), (vlan_id, code, data)

    def test_create_without_name(self, api_client):
        code, data = api_client.networks.create("", VLAN_ID)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("reason"), (code, data)

    @pytest.mark.parametrize("vlan_id", [4095])
    @pytest.mark.skip_if_version(
            "< v1.1.0", reason="https://github.com/harvester/harvester/issues/3151")
    def test_create_with_invalid_id(self, api_client, unique_name, vlan_id):
        code, data = api_client.networks.create(unique_name, vlan_id)

        assert 500 == code, (vlan_id, code, data)
        assert "InternalError" == data.get("reason"), (vlan_id, code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.networks
class TestNetworks:

    @pytest.mark.dependency(name="create_network_103")
    @pytest.mark.skip_if_version(">= v1.0.3")
    def test_create_103(self, api_client, unique_name):
        code, data = api_client.networks.create(unique_name, VLAN_ID)
        assert 201 == code, (code, data)

    @pytest.mark.dependency(name="create_network")
    @pytest.mark.skip_if_version(
            "< v1.1.0", reason="https://github.com/harvester/harvester/issues/3151")
    def test_create(self, api_client, unique_name):
        code, data = api_client.networks.create(unique_name, VLAN_ID, cluster_network='mgmt')
        assert 201 == code, (code, data)

    @pytest.mark.dependency(depends=["create_network_103", "create_network"], any=True)
    def test_get(self, api_client, unique_name):
        # Case 1: get all vlan networks
        code, data = api_client.networks.get()

        assert 200 == code, (code, data)
        assert len(data['items']) > 0, (code, data)

        # Case 2: get specific vlan by name
        code, data = api_client.networks.get(unique_name)

        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name'], (code, data)

    @pytest.mark.dependency(depends=["create_network_103", "create_network"], any=True)
    def test_delete(self, api_client, unique_name, wait_timeout):
        code, data = api_client.networks.delete(unique_name)

        assert 200 == code, (f"Failed to delete vlan with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.networks.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete vlan {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )
