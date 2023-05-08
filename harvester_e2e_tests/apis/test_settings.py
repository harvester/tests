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
import warnings

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.p0
@pytest.mark.settings
def test_get_all_settings(api_client, expected_settings):
    expected_settings = expected_settings['default']
    code, data = api_client.settings.get()

    available_settings = {m['metadata']['name'] for m in data['items']}

    assert 200 == code, (code, data)
    assert expected_settings <= available_settings, (
        "Some setting missing:\n"
        f"{expected_settings - available_settings}"
    )


@pytest.mark.p0
@pytest.mark.settings
@pytest.mark.skip_version_before('v1.1.0')
def test_get_all_settings_v110(api_client, expected_settings):
    expected_settings = expected_settings['default'] | expected_settings['1.1.0']
    code, data = api_client.settings.get()

    available_settings = {m['metadata']['name'] for m in data['items']}

    assert 200 == code, (code, data)
    assert expected_settings <= available_settings, (
        "Some setting missing:\n"
        f"{expected_settings - available_settings}"
    )

    removed = expected_settings - available_settings
    added = available_settings - expected_settings

    if removed:
        warnings.warn(UserWarning(f"Few setting(s) been removed: {removed}."))
    if added:
        warnings.warn(UserWarning(f"New setting(s) added: {added}"))


@pytest.mark.p0
@pytest.mark.settings
def test_update_log_level(api_client):
    code, data = api_client.settings.get("log-level")
    assert 200 == code, (f"Failed to get log-level setting with error: {code}, {data}")

    original_value = data.get("value", data['default'])
    updates = {"value": "Debug"}
    code, data = api_client.settings.update("log-level", updates)

    assert 200 == code, (f"Failed to update log-level setting with error: {code}, {data}")

    # For teardown
    updates = {"value": original_value}
    api_client.settings.update("log-level", updates)


@pytest.mark.p0
@pytest.mark.settings
def test_get_storage_network(api_client):
    code, data = api_client.settings.get("storage-network")
    assert 200 == code, (f"Failed to get storage-network setting with error: {code}, {data}")


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.settings
class TestUpdateInvalidStorageNetwork:
    invalid_vlan_id = 4095
    invalid_ip_range = "127.0.0.1/24"
    mgmt_network = "mgmt"

    def test_invalid_vlanid(self, api_client):
        spec = api_client.settings.StorageNetworkSpec.enable_with(
            self.invalid_vlan_id, self.mgmt_network, "192.168.1.0/24"
        )
        code, data = api_client.settings.update('storage-network', spec)

        assert 422 == code, (
            f"Storage Network should NOT able to create with VLAN ID: {self.invalid_vlan_id}\n"
            f"API Status({code}): {data}"
        )

    def test_invalid_iprange(self, api_client):
        valid_vlan_id = 1
        spec = api_client.settings.StorageNetworkSpec.enable_with(
            valid_vlan_id, self.mgmt_network, self.invalid_ip_range
        )
        code, data = api_client.settings.update('storage-network', spec)

        assert 422 == code, (
            f"Storage Network should NOT able to create with IP Range: {self.invalid_ip_range}\n"
            f"API Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.settings
class TestUpdateInvalidBackupTarget:
    def test_invalid_nfs(self, api_client):
        NFSSpec = api_client.settings.BackupTargetSpec.NFS

        spec = NFSSpec('not_starts_with_nfs://')
        code, data = api_client.settings.update('backup-target', spec)
        assert 422 == code, (
            f"NFS backup-target should check endpoint starting with `nfs://`\n"
            f"API Status({code}): {data}"
        )

        spec = NFSSpec('nfs://:/lack_server')
        code, data = api_client.settings.update('backup-target', spec)
        assert 422 == code, (
            f"NFS backup-target should check endpoint had server path\n"
            f"API Status({code}): {data}"
        )

        spec = NFSSpec('nfs://127.0.0.1:')
        code, data = api_client.settings.update('backup-target', spec)
        assert 422 == code, (
            f"NFS backup-target should check endpoint had mount path\n"
            f"API Status({code}): {data}"
        )

    def test_invalid_S3(self, api_client):
        S3Spec = api_client.settings.BackupTargetSpec.S3

        spec = S3Spec('bogus_bucket', 'bogus_region', 'bogus_key', 'bogus_secret')
        code, data = api_client.settings.update('backup-target', spec)
        assert 422 == code, (
            f"S3 backup-target should check key/secret/bucket/region"
            f"API Status({code}): {data}"
        )

        spec = S3Spec('', '', '', '', endpoint="http://127.0.0.1")
        code, data = api_client.settings.update('backup-target', spec)
        assert 422 == code, (
            f"S3 backup-target should check key/secret/bucket/region"
            f"API Status({code}): {data}"
        )
