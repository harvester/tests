import yaml
import pytest
import polling2
from time import sleep
from datetime import datetime, timedelta
from harvester_e2e_tests import utils
from urllib.parse import urljoin

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.images',
]


@pytest.fixture(scope="module")
def focal_image_url(request):
    base_url = request.config.getoption("--image-cache-url").strip()
    base_url = base_url or "https://cloud-images.ubuntu.com/focal/current/"
    return urljoin(f"{base_url}/", "focal-server-cloudimg-amd64.img")


@pytest.fixture(scope="module")
def focal_image(api_client, unique_name, wait_timeout, sleep_timeout, focal_image_url):
    image_name = f"img-focal-{unique_name}"
    msg = "Failed to upload image"

    code, data = api_client.images.create_by_url(image_name, focal_image_url)
    assert 201 == code, f"{msg}: {code}, {data}"

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(image_name)
        if 'status' in data and 'progress' in data['status'] and data['status']['progress'] == 100:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(f"{msg} ({wait_timeout}s timed out): {code}, {data}")

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user="ubuntu", id=f"{namespace}/{name}")

    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        # Wait until done so as not to affect futher TCs
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.images.get(image_name)
            if 404 == code:
                break
            sleep(sleep_timeout)


@pytest.fixture(scope="class")
def focal_vm(api_client, unique_name, wait_timeout, sleep_timeout, focal_image):
    vm_name = f"vm-focal-{unique_name}"
    msg = "Failed to create VM"

    vm_spec = api_client.vms.Spec(1, 2)
    vm_spec.add_image(vm_name, focal_image["id"])
    code, data = api_client.vms.create(vm_name, vm_spec)
    assert 201 == code, f"{msg}: {code}, {data}"

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(vm_name)
        vm_status = data.get('status', {}).get('printableStatus', '')
        if 200 == code and vm_status == "Running":
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(f"{msg} ({wait_timeout}s timed out): {code}, {data}")

    volumes = list(filter(lambda vol: "persistentVolumeClaim" in vol,
                          data["spec"]["template"]["spec"]["volumes"]))
    assert len(volumes) == 1
    yield data

    code, data = api_client.vms.get(vm_name)
    if 200 == code:
        api_client.vms.delete(vm_name)
        # Wait until done so as not to affect volume cleanup
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(vm_name)
            if 404 == code:
                break
            sleep(sleep_timeout)

    vol_name = volumes[0]['persistentVolumeClaim']['claimName']
    code, data = api_client.volumes.get(vol_name)
    if 200 == code:
        api_client.volumes.delete(vol_name)
        # Wait until done so as not to affect image cleanup
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(vol_name)
            if 404 == code:
                break
            sleep(sleep_timeout)


@pytest.mark.volumes
@pytest.mark.p1
def test_create_volume_image_form(volume_image_form):
    # NOTE: if the volume is successfully create that means the test is good
    """
    Volume test with image
    Covers:
        vol-03-Create volume root disk VM Image Form
    """
    pass


@pytest.mark.volumes
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


@pytest.mark.volumes
@pytest.mark.p1
class TestVolumeWithVM:
    def pause_vm(self, api_client, wait_timeout, sleep_timeout, focal_vm):
        vm_name = focal_vm['metadata']['name']
        msg = "Fail to Pause VM"

        code, data = api_client.vms.pause(vm_name)
        assert 204 == code, f"{msg}: {code}, {data}"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            conditions = data['status'].get('conditions', [])
            if conditions and conditions[-1].get('type') == "Paused":
                code, data = api_client.vms.get(vm_name)
                assert "Paused" == data['status']['printableStatus']
                break
            sleep(sleep_timeout)
        else:
            raise AssertionError(f"{msg} ({wait_timeout}s timed out): {code}, {data}")

    def stop_vm(self, api_client, wait_timeout, sleep_timeout, focal_vm):
        vm_name = focal_vm['metadata']['name']
        msg = "Fail to Stop VM"

        code, data = api_client.vms.stop(vm_name)
        assert 204 == code, f"{msg}: {code}, {data}"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get_status(vm_name)
            if 404 == code:
                break
            sleep(sleep_timeout)
        else:
            raise AssertionError(f"{msg} ({wait_timeout}s timed out): {code}, {data}")

    def delete_vm(self, api_client, wait_timeout, sleep_timeout, focal_vm):
        vm_name = focal_vm['metadata']['name']
        code, data = api_client.vms.delete(vm_name)
        msg = "Fail to Delete VM"
        assert 200 == code, f"{msg}: {code}, {data}"

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.vms.get(vm_name)
            if 404 == code:
                break
            sleep(sleep_timeout)
        else:
            raise AssertionError(f"{msg} ({wait_timeout}s timed out): {code}, {data}")

    def delete_volume_and_check_rc(self, api_client, focal_vm, expected_rc: int):
        volume = focal_vm["spec"]["template"]["spec"]["volumes"][0]
        vol_name = volume['persistentVolumeClaim']['claimName']
        code, data = api_client.volumes.delete(vol_name)
        assert expected_rc == code, \
            f"Delete volume should reply {expected_rc}: {code}, {data}"

    def test_delete_volume_bounded_on_existing_vm(self, api_client, wait_timeout, sleep_timeout,
                                                  focal_vm):
        """
        1. Create a VM with volume
        2. Delete volume should reply 422
        3. Pause VM
        4. Delete volume should reply 422 too
        5. Stop VM
        6. Delete volume should reply 422 too
        Ref. https://github.com/harvester/tests/issues/905
        """
        self.delete_volume_and_check_rc(api_client, focal_vm, 422)

        self.pause_vm(api_client, wait_timeout, sleep_timeout, focal_vm)
        self.delete_volume_and_check_rc(api_client, focal_vm, 422)

        self.stop_vm(api_client, wait_timeout, sleep_timeout, focal_vm)
        self.delete_volume_and_check_rc(api_client, focal_vm, 422)

    def test_delete_volume_bounded_on_deleted_vm(self, api_client, wait_timeout, sleep_timeout,
                                                 focal_vm):
        """
        1. Create a VM with volume
        2. Delete volume should reply 422
        3. Delete VM but not volume
        4. Delete volume should reply 200
        Ref. https://github.com/harvester/tests/issues/652
        """
        self.delete_volume_and_check_rc(api_client, focal_vm, 422)

        self.delete_vm(api_client, wait_timeout, sleep_timeout, focal_vm)
        self.delete_volume_and_check_rc(api_client, focal_vm, 200)


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


@pytest.mark.volumes
@pytest.mark.p1
def test_create_volume_backing_image(api_client, unique_name, image_opensuse,
                                     wait_timeout, sleep_timeout):
    """
    1. Create a new image from URL
    2. Check that it is created succesffully.
    3. Create a new volume with the image_id of the previous image
    4. Check that the new image is created
    5. Delete image and volume
    """

    code, image_data = api_client.images.create_by_url(unique_name, image_opensuse.url)

    assert 201 == code, (code, image_data)

    # This waits for the import to finish
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        image_conds = data.get('status', {}).get('conditions', [])
        if len(image_conds) > 0 and image_conds[0]['reason'] == 'Imported':
            break
        sleep(sleep_timeout)

    assert "Initialized" == image_conds[-1].get("type")
    assert "True" == image_conds[-1].get("status")
    spec = api_client.volumes.Spec("10Gi", f"longhorn-{image_data['spec']['displayName']}")
    image_id = f"{image_data['metadata']['namespace']}/{image_data['metadata']['name']}"
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id)
    assert 201 == code, (code, unique_name, data, image_id)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, volume_data = api_client.volumes.get(unique_name)
        assert 200 == code, (code, unique_name, volume_data)
        if volume_data['status']['phase'] == "Bound":
            break
        sleep(sleep_timeout)

    # This is for checking that the volume was created
    code, volume_data = api_client.volumes.get(unique_name)
    code, image_data = api_client.images.get(unique_name)
    assert 200 == code, (code, volume_data)
    assert unique_name == volume_data['metadata']['name'], (code, volume_data)
    assert volume_data['status']['phase'] == "Bound", (volume_data)
    assert image_id == volume_data['id'], (volume_data)
    api_client.volumes.delete(unique_name)
    api_client.images.delete(unique_name)
