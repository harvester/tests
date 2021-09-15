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
import polling2
import yaml
import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
]


def test_create_volume_missing_size(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    del request_json['spec']['resources']['requests']['storage']
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when attempting to create volume without '
        'specifying storage size: %s' % (resp.content))


def test_create_volume_missing_name(admin_session, harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    del request_json['metadata']['name']
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 422, (
        'Expected HTTP 422 when attempting to create volume without '
        'specifying a name: %s' % (resp.content))
    response_data = resp.json()
    assert 'name or generateName is required' in response_data['message']


def test_create_volumes(volume):
    # NOTE: if the volume is successfully create that means the test is good
    pass


def test_create_volume_image_form(volume_image_form):
    # NOTE: if the volume is successfully create that means the test is good
    pass


def test_create_volume_by_yaml(request, admin_session,
                               harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              data=yaml.dump(request_json, sort_keys=False),
                              headers={'Content-Type': 'application/yaml'})
    assert resp.status_code == 201, (
        'Failed to create volume with YAML request: %s' % (resp.content))
    view_endpoint = harvester_api_endpoints.get_volume % (
        request_json['metadata']['name'])
    validate_blank_volumes(request, admin_session, view_endpoint)
    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        request_json['metadata']['name']))
    # FIXME(gyee): we need to figure out why the API can arbitarily return
    # 200 or 204. It should consistently returning one.
    assert resp.status_code in [200, 204], 'Failed to delete volume: %s' % (
        resp.content)


def test_create_volume_using_image_by_yaml(request, admin_session,
                                           harvester_api_endpoints, image):
    request_json = utils.get_json_object_from_template('basic_volume')
    imageid = "/".join([image['metadata']['namespace'],
                       image['metadata']['name']])
    request_json['metadata']['annotations'][
        'harvesterhci.io/imageId'] = imageid
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              data=yaml.dump(request_json, sort_keys=False),
                              headers={'Content-Type': 'application/yaml'})
    assert resp.status_code == 201, (
        'Failed to create volume with YAML request: %s' % (resp.content))
    view_endpoint = harvester_api_endpoints.get_volume % (
        request_json['metadata']['name'])
    validate_blank_volumes(request, admin_session, view_endpoint)
    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        request_json['metadata']['name']))
    # FIXME(gyee): we need to figure out why the API can arbitarily return
    # 200 or 204. It should consistently returning one.
    assert resp.status_code in [200, 204], 'Failed to delete volume: %s' % (
        resp.content)


def test_create_volume_with_label(request, admin_session,
                                  harvester_api_endpoints):
    request_json = utils.get_json_object_from_template('basic_volume')
    request_json['metadata']['labels'] = {
        'test.harvesterhci.io': 'for-test'
    }
    resp = admin_session.post(harvester_api_endpoints.create_volume,
                              json=request_json)
    assert resp.status_code == 201, (
        'Failed to create volume with labels: %s' % (resp.content))
    view_endpoint = harvester_api_endpoints.get_volume % (
        request_json['metadata']['name'])
    pvc_json = validate_blank_volumes(request, admin_session, view_endpoint)
    assert pvc_json['metadata']['labels'].get(
        'test.harvesterhci.io') == 'for-test'
    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        request_json['metadata']['name']))
    # FIXME(gyee): we need to figure out why the API can arbitarily return
    # 200 or 204. It should consistently returning one.
    assert resp.status_code in [200, 204], 'Failed to delete volume: %s' % (
        resp.content)


def test_create_volume_with_image_label(volume_with_image):
    # NOTE: if the volume is successfully create that means the test is good
    pass


def test_update_volume_json(request, admin_session,
                            harvester_api_endpoints, volume):
    view_endpoint = harvester_api_endpoints.get_volume % (
        volume['metadata']['name'])
    pvc_json = validate_blank_volumes(request, admin_session, view_endpoint)
    # now try to increase the size
    pvc_json['spec']['resources']['requests']['storage'] = '21Gi'
    resp = utils.poll_for_update_resource(
        request, admin_session,
        harvester_api_endpoints.update_volume % (
            volume['metadata']['name']),
        pvc_json,
        harvester_api_endpoints.get_volume % (
            volume['metadata']['name']))
    validate_blank_volumes(request, admin_session, view_endpoint)
    updated_vol_data = resp.json()
    assert updated_vol_data['spec']['resources']['requests'].get(
        'storage') == '21Gi'


def test_update_volume_yaml(request, admin_session,
                            harvester_api_endpoints, volume):
    view_endpoint = harvester_api_endpoints.get_volume % (
        volume['metadata']['name'])
    pvc_json = validate_blank_volumes(request, admin_session, view_endpoint)
    # now try to increase the size
    pvc_json['spec']['resources']['requests']['storage'] = '22Gi'
    resp = utils.poll_for_update_resource(
        request, admin_session,
        harvester_api_endpoints.update_volume % (
            volume['metadata']['name']),
        pvc_json,
        harvester_api_endpoints.get_volume % (
            volume['metadata']['name']),
        use_yaml=True)
    validate_blank_volumes(request, admin_session, view_endpoint)
    updated_vol_data = resp.json()
    assert updated_vol_data['spec']['resources']['requests'].get(
        'storage') == '22Gi'


def validate_blank_volumes(request, admin_session, get_api_link):
    pvc_json = None

    def _wait_for_volume_ready():
        nonlocal pvc_json
        resp = admin_session.get(get_api_link)
        if resp.status_code == 200:
            pvc_json = resp.json()
            if 'status' in pvc_json and pvc_json['status']['phase'] == 'Bound':
                return True
        return False

    success = polling2.poll(
        _wait_for_volume_ready,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for volume to be ready.'
    return pvc_json


@pytest.mark.terraform
def test_create_volume_using_terraform(admin_session, volume_using_terraform):
    # NOTE: the volume_using_terraform fixture will be creating the
    # volume and check the result
    pass


@pytest.mark.terraform
def test_create_vol_with_image_terraform(admin_session,
                                         volume_with_image_using_terraform):
    # NOTE: the volume_using_terraform fixture will be creating the
    # volume and check the result
    pass
