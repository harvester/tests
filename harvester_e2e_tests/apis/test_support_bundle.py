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
import tarfile
from io import BytesIO
from time import sleep
from zipfile import ZipFile
from datetime import datetime, timedelta

import yaml
import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


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

    @pytest.mark.dependency(name="donwnload support bundle", depends=["get support bundle"])
    def test_download(self, api_client, support_bundle_state, wait_timeout):

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.supportbundle.get(support_bundle_state.uid)
            if 100 == data.get('status', {}).get('progress', 0):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to wait supportbundle ready with {wait_timeout} timed out\n"
                f"Still got {code} in {data}"
            )

        code, ctx = api_client.supportbundle.download(support_bundle_state.uid)

        assert 200 == code, (code, ctx)

        with ZipFile(BytesIO(ctx), 'r') as zf:
            files = zf.namelist()

        assert 0 != len(files)

        support_bundle_state.files = files
        support_bundle_state.fio.write(ctx)
        support_bundle_state.fio.seek(0)

    @pytest.mark.dependency(depends=["donwnload support bundle"])
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

    @pytest.mark.dependency(depends=["donwnload support bundle"])
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

    @pytest.mark.dependency(depends=["donwnload support bundle"])
    def test_secret_file_exists(self, support_bundle_state):
        ''' ref: https://github.com/harvester/tests/issues/603 '''
        pattern = r"^.*/yamls/namespaced/fleet-local/v1/secrets\.yaml"
        for fname in support_bundle_state.files:
            if re.match(pattern, fname):
                break
        else:
            raise AssertionError("secret file is not available in namespaced/fleet-local")

        with ZipFile(support_bundle_state.fio, 'r') as zf:
            ctx = zf.read(fname)
        support_bundle_state.fio.seek(0)

        secret = yaml.safe_load(ctx)
        assert secret.get('items')

        fails = []
        for it in secret['items']:
            if it.get('type') != "rke.cattle.io/machine-plan" or not it.get('data'):
                fails.append(it)

        assert not fails, (
            f"Got {len(fails)} incorrect item(s) from secret file,"
            " expected type should be 'rke.cattle.io/machine-plan'"
            " and `data` field should not be empty but got:\n"
            f"{fails}"
        )

    @pytest.mark.dependency(depends=["donwnload support bundle"])
    def test_hardware_info_exists(self, support_bundle_state):
        ''' ref: https://github.com/harvester/tests/issues/569 '''
        nodes, pattern = [], r"^.*/nodes/.*.zip"

        for fname in support_bundle_state.files:
            if re.match(pattern, fname):
                nodes.append(fname)
        assert nodes, "Host information is not generated"

        with ZipFile(support_bundle_state.fio, 'r') as zf:
            b_nodes = [zf.read(n) for n in nodes]
        support_bundle_state.fio.seek(0)

        fails, txz_pattern = [], r"^.*/scc_supportconfig.*.txz"
        for npath, node_byte in zip(nodes, b_nodes):
            node_name = npath.rsplit("/", 1)[-1]
            with ZipFile(BytesIO(node_byte), 'r') as zf:
                try:
                    txz_file = next(i for i in zf.namelist() if re.match(txz_pattern, i))
                    txz_byte = zf.read(txz_file)
                except StopIteration:
                    fails.append(f"`.txz` file is not available in {node_name}")
                    continue
                try:
                    with tarfile.open(mode="r:xz", fileobj=BytesIO(txz_byte)) as xz:
                        txt_m = next(m for m in xz.getmembers() if m.name.endswith("hardware.txt"))
                        hardware_ctx = xz.extractfile(txt_m).read().decode()
                except StopIteration:
                    fails.append(f"`hardware.txt` file is not available in {node_name}")
                    continue

            if "lsusb" not in hardware_ctx or "hwinfo" not in hardware_ctx:
                fails.append(
                    f"Node {node_name}'s Hardware info not contains lsusb/hwinfo command ouput\n"
                    f"got: {hardware_ctx}"
                )

        assert not fails, (
            f"Got {len(fails)} incorrect item(s):\n"
            "\n".join(fails)
        )

    @pytest.mark.dependency(depends=["get support bundle"])
    def test_delete(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.delete(support_bundle_state.uid)

        # ???: Downloaded support bundle will be deleted automatically
        assert 404 == code, (code, data)
