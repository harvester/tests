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

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.p1
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


@pytest.mark.p1
@pytest.mark.negative
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
            if 100 == data['status'].get('progress', 0):
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

    @pytest.mark.dependency(depends=["get support bundle"])
    def test_delete(self, api_client, support_bundle_state):
        code, data = api_client.supportbundle.delete(support_bundle_state.uid)

        # ???: Downloaded support bundle will be deleted automatically
        assert 404 == code, (code, data)
