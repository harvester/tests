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
import time
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.backuptarget'
]


@pytest.mark.backups3
def test_setup_backup_target_s3(backuptarget_s3):
    # NOTE: if the backuptarget is successfully create that means the
    # test is good
    pass


@pytest.mark.backupnfs
def test_setup_backup_target_nfs(backuptarget_nfs):
    # NOTE: if the backuptarget is successfully create that means the
    # test is good
    pass


@pytest.mark.backupnfs
def test_invalid_backup_target_nfs(request, admin_session,
                                   harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    request_json = utils.get_json_object_from_template(
        'backup_target',
        storetype='nfs',
        endpoint='nfs://',
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
    time.sleep(30)
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    assert backup_target_data['metadata']['state']['error'], (
        'Backup Target Failed with error: %s' % (
            backup_target_data['metadata']['state']['message']))
    assert 'NFS path must follow: nfs://server:/path/ format' in (
        backup_target_data['metadata']['state']['message'])


@pytest.mark.backups3
def test_invalid_backup_target_s3(request, admin_session,
                                  harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    request_json = utils.get_json_object_from_template(
        'backup_target',
        storetype='s3',
        endpoint='',
        accesskeyid='bogus',
        secretaccesskey='bogus',
        bucketname='bogus',
        region='us-east-2'
    )
    resp = utils.poll_for_update_resource(
        request, admin_session,
        backup_target_data['links']['update'],
        request_json,
        harvester_api_endpoints.get_backup_target)
    updated_settings_data = resp.json()
    assert updated_settings_data['value'] == request_json['value'], (
        'Failed to update Backup Target with S3')
    time.sleep(30)
    resp = admin_session.get(harvester_api_endpoints.get_backup_target)
    assert resp.status_code == 200, (
        'Failed to get Backup Target Settings: %s' % (resp.content))
    backup_target_data = resp.json()
    assert backup_target_data['metadata']['state']['error'], (
        'Backup Target Failed with error: %s' % (
            backup_target_data['metadata']['state']['message']))
    assert 'operation error S3: ListBucket' in (
        backup_target_data['metadata']['state']['message'])
