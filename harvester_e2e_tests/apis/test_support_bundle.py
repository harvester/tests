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

import json
import os
import re
import tempfile
import zipfile

import polling2
import pytest
from harvester_e2e_tests import utils

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.user',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.support_bundle'
]


def _create_bundle(admin_session, harvester_api_endpoints):
    """Helper function to create 'happy path' support bundle

    Args:
        admin_session (dict): fixture that gets exteneded from requests
        harvester_api_endpoints (dict): constants harvester api endpoints
    """
    request_json = utils.get_json_object_from_template('support_bundle')
    resp = admin_session.post(
        harvester_api_endpoints.create_support_bundle, json=request_json)
    assert resp.status_code == 201
    resp_json = json.loads(resp.text)
    name = resp_json.get('metadata').get('name')
    return name, resp_json


def test_create_missing_description(
        admin_session, harvester_api_endpoints):
    """Tests that description is enforced on support bundle creation

    Args:
        admin_session (dict): fixture that gets exteneded from requests
        harvester_api_endpoints (dict): constants harvester api endpoints
    """
    request_json = utils.get_json_object_from_template('support_bundle')
    del request_json['spec']['description']
    resp = admin_session.post(
        harvester_api_endpoints.create_support_bundle, json=request_json)
    assert resp.status_code == 422
    assert 'is invalid: spec.description: Required value' in resp.text


def test_delete(admin_session, harvester_api_endpoints):
    """Tests creating a support bundle then it's deletion

    Args:
        admin_session (dict): fixture that gets exteneded from requests
        harvester_api_endpoints (dict): constants harvester api endpoints
    """
    name, _resp_json = _create_bundle(admin_session, harvester_api_endpoints)
    delete_resp = admin_session.delete(
        harvester_api_endpoints.delete_support_bundle + name
    )
    assert delete_resp.status_code == 200


@pytest.mark.p1
@pytest.mark.slow
def test_creates_successful_bundle_and_downloads(
        admin_session, harvester_api_endpoints):
    """Creates a support bundle, validates it progresses to 100%,
    downloads in memory as a zip file, audits the zip file to
    ensure all needed files are present

    Args:
        admin_session (dict): fixture that gets exteneded from requests
        harvester_api_endpoints (dict): constants harvester api endpoints
    """
    name, _resp_json = _create_bundle(admin_session, harvester_api_endpoints)
    progress = 0

    def _wait_for_progress_to_be_ready():
        nonlocal progress
        resp_progress_check = admin_session.get(
            harvester_api_endpoints.view_support_bundle +
            name)
        json_progress_result = json.loads(resp_progress_check.text)
        progress = json_progress_result.get('status', {}).get('progress', 0)
        if progress != 100:
            return False
        return True

    try:
        polling2.poll(
            _wait_for_progress_to_be_ready,
            step=5,
            timeout=300
        )
    except Exception as ex:
        raise f'Timed out waiting for support bundle: {ex}'

    temp_dir = tempfile.mkdtemp()
    zip_file_location = os.path.join(temp_dir, 'support_bundle.zip')
    resp_download = admin_session.get(
        harvester_api_endpoints.download_support_bundle +
        name +
        '/download')
    with open(zip_file_location, 'wb') as zip_file:
        zip_file.write(resp_download.content)
    files = None
    with zipfile.ZipFile(zip_file_location, 'r') as zip_file:
        files = zip_file.namelist()

    patterns = [r"^.*/logs/cattle-fleet-local-system/fleet-agent-.*/fleet-agent.log",
                r"^.*/logs/cattle-fleet-system/fleet-controller-.*/fleet-controller.log",
                r"^.*/logs/cattle-fleet-system/gitjob-.*/gitjob.log"]
    matches = []
    for f in files:
        for pattern in patterns:
            matches.extend([f] if re.match(pattern, f) else [])
            print(f)
            print(pattern)

    err_msg = ("Some file(s) not found,"
               f"files: {matches}\n"
               f"patterns: {patterns}")
    assert len(matches) == len(patterns), err_msg
