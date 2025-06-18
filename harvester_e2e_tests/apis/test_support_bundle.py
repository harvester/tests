# Copyright (c) 2022 SUSE LLC
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
from io import BytesIO
from time import sleep
from zipfile import ZipFile
from datetime import datetime, timedelta

import yaml
import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


def wait_for_support_bundle_condition(
    api_client, uid, condition_check, wait_timeout, timeout_message
):
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.supportbundle.get(uid)
        if condition_check(data):
            return code, data
        sleep(5)
    else:
        raise AssertionError(
            f"{timeout_message} with {wait_timeout} timed out\n"
            f"Still got {code} in {data}"
        )


def wait_for_support_bundle_ready(api_client, uid, wait_timeout):
    return wait_for_support_bundle_condition(
        api_client,
        uid,
        lambda data: 100 == data.get('status', {}).get('progress', 0),
        wait_timeout,
        "Failed to wait supportbundle ready"
    )


def wait_for_support_bundle_error(api_client, uid, wait_timeout):
    return wait_for_support_bundle_condition(
        api_client,
        uid,
        lambda data: data.get('status', {}).get('state') == "error",
        wait_timeout,
        "Failed to wait supportbundle error state"
    )


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.negative
@pytest.mark.support_bundle
class TestSupportBundleNegative:
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.supportbundle.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.supportbundle.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.support_bundle
class TestSupportBundle:
    @pytest.mark.dependency(name="create support bundle")
    def test_create(self, api_client, unique_name, support_bundle_state):
        code, data = api_client.supportbundle.create(unique_name)

        assert 201 == code, (code, data)

        support_bundle_state.uid = data['metadata']['name']

    @pytest.mark.dependency(name="get support bundle", depends=["create support bundle"])
    def test_get(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.get(support_bundle_state.uid)

        assert 200 == code, (code, data)

    @pytest.mark.dependency(name="download support bundle", depends=["get support bundle"])
    def test_download(self, api_client, support_bundle_state, wait_timeout):
        wait_for_support_bundle_ready(api_client, support_bundle_state.uid, wait_timeout)

        code, ctx = api_client.supportbundle.download(support_bundle_state.uid)

        assert 200 == code, (code, ctx)

        with ZipFile(BytesIO(ctx), 'r') as zf:
            files = zf.namelist()

        assert 0 != len(files)

        support_bundle_state.files = files
        support_bundle_state.fio.write(ctx)
        support_bundle_state.fio.seek(0)

    @pytest.mark.dependency(depends=["download support bundle"])
    def test_logfile_exists(self, support_bundle_state):
        patterns = [r"^.*/logs/cattle-fleet-local-system/fleet-agent-.*/fleet-agent.log",
                    r"^.*/logs/cattle-fleet-system/fleet-controller-.*/fleet-controller.log",
                    r"^.*/logs/cattle-fleet-system/gitjob-.*/gitjob.log"]
        matches = []
        for f in support_bundle_state.files:
            for pattern in patterns:
                matches.extend([f] if re.match(pattern, f) else [])

        assert len(matches) == len(patterns), (
            f"Some file(s) not found, files: {matches}\npatterns: {patterns}"
        )

    @pytest.mark.dependency(depends=["download support bundle"])
    def test_plan_secrets_exists(self, support_bundle_state):
        # ref: https://github.com/harvester/tests/issues/603
        path = r"^.*/yamls/namespaced/fleet-local/v1/secrets.yaml"

        for fname in support_bundle_state.files:
            if re.match(path, fname):
                break
        else:
            raise AssertionError(f"{path} not existed")

        try:
            with ZipFile(support_bundle_state.fio, 'r') as zf:
                with zf.open(fname) as file:
                    secrets = yaml.safe_load(file)
            assert all('rke.cattle.io/machine-plan' == o['type'] for o in secrets['items']), (
                "secrets got unexpected type:\n"
                f"{[o['type'] for o in secrets['items']]}"
            )
        finally:
            support_bundle_state.fio.seek(0)

    @pytest.mark.dependency(depends=["get support bundle"])
    def test_delete(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.delete(support_bundle_state.uid)

        # After download, the support bundle will be deleted automatically
        assert 404 == code, (code, data)


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.negative
@pytest.mark.support_bundle
@pytest.mark.skip_version_if("< v1.6.0", reason="Issue#7835 new feature in v1.6.0")
class TestSupportBundleInvalidExtraCollectionNamespaces:
    def test_create_invalid_extra_collection_namespaces(
        self, api_client, unique_name, support_bundle_state
    ):
        """
        1. Tries to create a support bundle with invalid extra collection namespaces
        2. Checks that it gets a 400
        """
        code, data = api_client.supportbundle.create(
            unique_name,
            extra_collection_namespaces=["invalid-namespace"]
        )

        assert 400 == code, (code, data)
        assert 'namespace invalid-namespace not found' in data.get("message", ""), (code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.support_bundle
@pytest.mark.skip_version_if("< v1.6.0", reason="Issue#7835 new feature in v1.6.0")
class TestSupportBundleTimeout:
    @pytest.mark.dependency(name="create support bundle")
    def test_create(self, api_client, unique_name, support_bundle_state):
        code, data = api_client.supportbundle.create(unique_name, timeout=1)

        assert 201 == code, (code, data)

        support_bundle_state.uid = data['metadata']['name']

    @pytest.mark.dependency(name="get support bundle", depends=["create support bundle"])
    def test_get(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.get(support_bundle_state.uid)

        assert 200 == code, (code, data)

    @pytest.mark.dependency(name="process support bundle", depends=["get support bundle"])
    def test_process_timeout(self, api_client, support_bundle_state, wait_timeout):
        wait_for_support_bundle_error(
            api_client, support_bundle_state.uid, wait_timeout
        )

    @pytest.mark.dependency(depends=["process support bundle"])
    def test_delete(self, api_client, support_bundle_state):
        # After timeout, the support bundle should be deleted manually
        code, data = api_client.supportbundle.delete(support_bundle_state.uid)
        assert 200 == code, (code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.support_bundle
@pytest.mark.skip_version_if("< v1.6.0", reason="Issue#7835 new feature in v1.6.0")
class TestSupportBundleExpiration:
    @pytest.mark.dependency(name="create support bundle")
    def test_create(self, api_client, unique_name, support_bundle_state):
        code, data = api_client.supportbundle.create(unique_name, expiration=1)

        assert 201 == code, (code, data)

        support_bundle_state.uid = data['metadata']['name']

    @pytest.mark.dependency(name="get support bundle", depends=["create support bundle"])
    def test_get(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.get(support_bundle_state.uid)

        assert 200 == code, (code, data)

    @pytest.mark.dependency(name="process support bundle", depends=["get support bundle"])
    def test_download_expiration(self, api_client, support_bundle_state, wait_timeout):
        code, data = wait_for_support_bundle_ready(
            api_client, support_bundle_state.uid, wait_timeout
        )

        expiration = data.get('spec', {}).get('expiration', 0)  # unit is minute
        sleep(expiration * 60 + 10)  # 10 seconds more to ensure expiration

        # After expiration, the support bundle should be deleted automatically
        code, data = api_client.supportbundle.get(support_bundle_state.uid)
        assert 404 == code, (code, data)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.support_bundle
@pytest.mark.skip_version_if("< v1.6.0", reason="Issue#7835 new feature in v1.6.0")
class TestSupportBundleExtraNamespaces:
    @pytest.mark.dependency(name="create support bundle")
    def test_create(self, api_client, unique_name, support_bundle_state):
        code, data = api_client.supportbundle.create(
            unique_name,
            extra_collection_namespaces=["kube-system"],
        )

        assert 201 == code, (code, data)

        support_bundle_state.uid = data['metadata']['name']

    @pytest.mark.dependency(name="get support bundle", depends=["create support bundle"])
    def test_get(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.get(support_bundle_state.uid)

        assert 200 == code, (code, data)

    @pytest.mark.dependency(name="download support bundle", depends=["get support bundle"])
    def test_download(self, api_client, support_bundle_state, wait_timeout):
        wait_for_support_bundle_ready(api_client, support_bundle_state.uid, wait_timeout)

        code, ctx = api_client.supportbundle.download(support_bundle_state.uid)

        assert 200 == code, (code, ctx)

        with ZipFile(BytesIO(ctx), 'r') as zf:
            files = zf.namelist()

        assert 0 != len(files)

        support_bundle_state.files = files
        support_bundle_state.fio.write(ctx)
        support_bundle_state.fio.seek(0)

    @pytest.mark.dependency(depends=["download support bundle"])
    def test_logfile_exists(self, support_bundle_state):
        patterns = [r"^.*/logs/kube-system/kube-apiserver-.*/kube-apiserver.log",]
        matches = []
        for f in support_bundle_state.files:
            for pattern in patterns:
                matches.extend([f] if re.match(pattern, f) else [])

        assert len(matches) == len(patterns), (
            f"Some file(s) not found, files: {matches}\npatterns: {patterns}"
        )

    @pytest.mark.dependency(depends=["get support bundle"])
    def test_delete(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.delete(support_bundle_state.uid)

        # After download, the support bundle will be deleted automatically
        assert 404 == code, (code, data)
