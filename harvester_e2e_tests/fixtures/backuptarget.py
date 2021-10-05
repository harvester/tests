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

from harvester_e2e_tests import utils
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.api_version',
    'harvester_e2e_tests.fixtures.session',
]


@pytest.fixture(scope='class')
def backuptarget_s3(request, kubevirt_api_version, admin_session,
                    harvester_api_endpoints):
    accesskey = request.config.getoption('--accessKeyId')
    secretaccesskey = request.config.getoption('--secretAccessKey')
    bucket = request.config.getoption('--bucketName')
    region = request.config.getoption('--region')
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    store_type = "s3"
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    request_json = utils.get_json_object_from_template(
        'backup_target',
        storetype=store_type,
        endpoint='',
        accesskeyid=accesskey,
        secretaccesskey=secretaccesskey,
        bucketname=bucket,
        region=region
    )
    resp = utils.poll_for_update_resource(
        request, admin_session,
        backup_target_data['links']['update'],
        request_json,
        harvester_api_endpoints.get_backup_target)
    updated_settings_data = resp.json()
    assert updated_settings_data['value'] == request_json['value'], (
        'Failed to update Backup Target with S3')
    yield updated_settings_data


@pytest.fixture(scope='class')
def backuptarget_nfs(request, kubevirt_api_version, admin_session,
                     harvester_api_endpoints):
    nfs_endpoint = request.config.getoption('--nfs-endpoint')
    store_type = "nfs"
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    request_json = utils.get_json_object_from_template(
        'backup_target',
        storetype=store_type,
        endpoint=nfs_endpoint,
        accesskeyid='',
        secretaccesskey='',
        bucketname='',
        region=''
    )
    resp = utils.poll_for_update_resource(
        request, admin_session,
        backup_target_data['links']['update'],
        request_json,
        harvester_api_endpoints.get_backup_target)
    updated_settings_data = resp.json()
    assert updated_settings_data['value'] == request_json['value'], (
        'Failed to update Backup Target with NFS')
    yield updated_settings_data
