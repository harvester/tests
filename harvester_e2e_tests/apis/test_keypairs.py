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


@pytest.mark.p1
@pytest.mark.negative
@pytest.mark.keypairs
class TestKeypairsNegative:
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.keypairs.get(unique_name)
        assert code == 404
        assert "NotFound" == data.get("reason")

    @pytest.mark.dependency(name="delete_keypair_negative")
    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.keypairs.delete(unique_name, "namespace")
        assert code == 404
        assert "NotFound" == data.get("reason")

    @pytest.mark.dependency(name="create_keypair_negative")
    def test_create_with_empty_name(self, api_client, ssh_keypair):
        pubkey, prikey = ssh_keypair
        code, data = api_client.keypairs.create("", pubkey)

        assert code == 422, "Expecting got 422 when keypair name is empty"
        assert "Invalid" in data.get("reason")

    def test_create_with_empty_key(self, api_client, unique_name):
        code, data = api_client.keypairs.create(unique_name, "")

        assert code == 422, "Expecting got 422 when publicKey is empty"
        assert "Invalid" in data.get("reason")

    def test_create_with_invalid_key(self, api_client, unique_name):
        code, data = api_client.keypairs.create(unique_name, "INVALID_PUBLIC_KEY")

        assert code == 422, "Expecting got 422 when publicKey is empty"
        assert "Invalid" in data.get("reason")


@pytest.mark.p1
@pytest.mark.keypairs
class TestKeypairs:
    @pytest.mark.dependency(depends=["delete_keypair_negative", "create_keypair_negative"],
                            name="create_keypairs")
    def test_create(self, api_client, ssh_keypair, unique_name):
        public, private = ssh_keypair
        status_code, data = api_client.keypairs.create(unique_name, public)

        assert status_code == 201, (
            f"Unable to create Keypair `{unique_name}` with `{public}`\n"
            f"Response: {data}"
        )
        assert public == data['spec']['publicKey'], (
            f"public key does not match: `{public}`\n"
            f"responsed: `{data['spec']['publicKey']}`"
        )

        # 5 mins for cluster to validate keypair
        endtime = datetime.now() + timedelta(minutes=5)
        while endtime > datetime.now():
            status_code, data = api_client.keypairs.get(unique_name)
            if "validated" == data.get("status", {}).get("conditions", [{}])[0].get('type'):
                break
            sleep(5)
        else:
            raise AssertionError(f"Cluster failed to validate keypair `{unique_name}` in 5 mins")

    @pytest.mark.dependency(depends=["create_keypairs"])
    def test_get(self, api_client, ssh_keypair, unique_name):
        # Case 1: get all keypairs
        status_code, data = api_client.keypairs.get()

        assert len(data['items']) > 0, (status_code, data)

        # Case 2: get created keypairs
        status_code, data = api_client.keypairs.get(unique_name)
        pubkey, _ = ssh_keypair

        assert unique_name == data['metadata'].get('name')
        assert pubkey == data['spec']['publicKey']

    @pytest.mark.dependency(depends=["create_keypairs"])
    def test_delete(self, api_client, unique_name):
        status_code, data = api_client.keypairs.delete(unique_name)

        assert 200 == status_code, (status_code, data)
        assert "Success" == data['status']

        status_code, data = api_client.keypairs.get(unique_name)

        assert 404 == status_code, (status_code, data)
