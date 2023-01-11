import yaml
import pytest
import polling2
from time import sleep
from datetime import datetime, timedelta
from harvester_e2e_tests import utils

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.images',
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


@pytest.mark.volumes_p1
@pytest.mark.p1
@pytest.mark.dependency(depends=["create_with_url"])
def test_create_volume_backing_image(api_client, unique_name, opensuse_image, wait_timeout):
    """
    1. Create a new image from URL
    2. Check that it is created succesffully.
    3. Create a new volume with the image_id of the previous image
    4. Check that the new image is created
    5. Delete image and volume
    """

    code, image_data = api_client.images.create_by_url(unique_name, opensuse_image.url)
    if code != 201:
        raise AssertionError(
            f"Failed to create image {unique_name} from URL got\n"
            f"Creation got {code} with {image_data}"
        )

    assert 201 == code, (code, image_data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        image_conds = data.get('status', {}).get('conditions', [])
        if len(image_conds) > 0:
            break
        sleep(3)

    assert "Initialized" == image_conds[-1].get("type")
    assert "True" == image_conds[-1].get("status")
    spec = api_client.volumes.Spec(1)
    spec.size = "10Gi"
    # spec.storage_cls = "longhorn-" + image_data["spec"]["displayName"]
    image_id_temp = image_data["metadata"]["namespace"] + '/' + image_data["metadata"]["name"]
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id_temp)

    # This is for checking that the volume was created
    code, volume_data = api_client.volumes.get(unique_name)
    assert 200 == code, (code, volume_data)
    assert unique_name == volume_data['metadata']['name'], (code, volume_data)
    assert image_id_temp == volume_data['id']

    api_client.images.delete(unique_name)
    api_client.volumes.delete(unique_name)
