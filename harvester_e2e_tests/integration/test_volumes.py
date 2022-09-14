import yaml
import pytest
import polling2

from harvester_e2e_tests import utils

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
]


@pytest.mark.volumes_p1
@pytest.mark.p1
def test_create_volume_image_form(volume_image_form):
    # NOTE: if the volume is successfully create that means the test is good
    """
    Volume test with image
    Covers:
        vol-03-Create volume root disk VM Image Form
    """
    pass


@pytest.mark.volumes_p1
@pytest.mark.p1
def test_create_volume_using_image_by_yaml(request, admin_session,
                                           harvester_api_endpoints, image):
    """
    Volume test with image
    Covers:
        vol-04-Create volume root disk VM Image YAML
    """
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
