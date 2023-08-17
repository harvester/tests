import yaml
import pytest
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
def focal_image(api_client, unique_name, focal_image_url, polling_for):
    image_name = f"img-focal-{unique_name}"

    code, data = api_client.images.create_by_url(image_name, focal_image_url)
    assert 201 == code, f"Fail to create image\n{code}, {data}"
    code, data = polling_for("image do created",
                             lambda c, d: c == 200 and d.get('status', {}).get('progress') == 100,
                             api_client.images.get, image_name)

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user="ubuntu", id=f"{namespace}/{name}")

    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        assert 200 == code, f"Fail to cleanup image\n{code}, {data}"
        polling_for("image do deleted",
                    lambda c, d: 404 == c,
                    api_client.images.get, image_name)


@pytest.fixture(scope="class")
def focal_vm(api_client, unique_name, focal_image, polling_for):
    vm_name = f"vm-focal-{unique_name}"

    vm_spec = api_client.vms.Spec(1, 2)
    vm_spec.add_image(vm_name, focal_image["id"])
    code, data = api_client.vms.create(vm_name, vm_spec)
    assert 201 == code, f"Fail to create VM\n{code}, {data}"
    code, data = polling_for(
        "VM do created",
        lambda c, d: 200 == c and d.get('status', {}).get('printableStatus') == "Running",
        api_client.vms.get, vm_name
    )

    volumes = list(filter(lambda vol: "persistentVolumeClaim" in vol,
                          data["spec"]["template"]["spec"]["volumes"]))
    assert len(volumes) == 1
    yield data

    code, data = api_client.vms.get(vm_name)
    if 200 == code:
        code, data = api_client.vms.delete(vm_name)
        assert 200 == code, f"Fail to cleanup VM\n{code}, {data}"
        polling_for("VM do deleted",
                    lambda c, d: 404 == c,
                    api_client.vms.get, vm_name)

    vol_name = volumes[0]['persistentVolumeClaim']['claimName']
    code, data = api_client.volumes.get(vol_name)
    if 200 == code:
        api_client.volumes.delete(vol_name)
        assert 200 == code, f"Fail to cleanup volume\n{code}, {data}"
        polling_for("volume do deleted",
                    lambda c, d: 404 == c,
                    api_client.volumes.get, vol_name)


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
def test_create_volume_using_image_by_yaml(admin_session, harvester_api_endpoints, image,
                                           polling_for):
    """
    Volume test with image
    Covers:
        vol-04-Create volume root disk VM Image YAML
    """
    def _validate_blank_volumes(admin_session, get_api_link):
        resp = admin_session.get(get_api_link)
        return resp.status_code, resp.json()

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

    polling_for("volume to be ready",
                lambda c, d: 200 == c and 'status' in d and d['status']['phase'] == 'Bound',
                _validate_blank_volumes, admin_session, view_endpoint)

    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        request_json['metadata']['name']))
    # FIXME(gyee): we need to figure out why the API can arbitarily return
    # 200 or 204. It should consistently returning one.
    assert resp.status_code in [200, 204], 'Failed to delete volume: %s' % (
        resp.content)


@pytest.mark.volumes
@pytest.mark.p1
def test_create_volume_backing_image(api_client, unique_name, image_opensuse, polling_for):
    """
    1. Create a new image from URL
    2. Check that it is created succesffully.
    3. Create a new volume with the image_id of the previous image
    4. Check that the new image is created
    5. Delete image and volume
    """
    def _get_image_conds(image_name):
        code, data = api_client.images.get(image_name)
        return data.get('status', {}).get('conditions', [])

    code, image_data = api_client.images.create_by_url(unique_name, image_opensuse.url)
    assert 201 == code, (code, image_data)

    image_conds = polling_for(
        "image do imported",
        lambda image_conds: len(image_conds) > 0 and image_conds[0]['reason'] == 'Imported',
        _get_image_conds, unique_name
    )
    assert "Initialized" == image_conds[-1].get("type")
    assert "True" == image_conds[-1].get("status")

    spec = api_client.volumes.Spec("10Gi", f"longhorn-{image_data['spec']['displayName']}")
    image_id = f"{image_data['metadata']['namespace']}/{image_data['metadata']['name']}"
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id)
    assert 201 == code, (code, unique_name, data, image_id)

    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)
    code, volume_data = api_client.volumes.get(unique_name)
    code, image_data = api_client.images.get(unique_name)
    assert 200 == code, (code, volume_data)
    assert unique_name == volume_data['metadata']['name'], (code, volume_data)
    assert volume_data['status']['phase'] == "Bound", (volume_data)
    assert image_id == volume_data['id'], (volume_data)

    api_client.volumes.delete(unique_name)
    api_client.images.delete(unique_name)


@pytest.mark.volumes
@pytest.mark.p1
class TestVolumeWithVM:
    def pause_vm(self, api_client, focal_vm, polling_for):
        vm_name = focal_vm['metadata']['name']
        code, data = api_client.vms.pause(vm_name)
        assert 204 == code, f"Fail to pause VM\n{code}, {data}"
        polling_for("VM do paused",
                    lambda c, d: d.get('status', {}).get('printableStatus') == "Paused",
                    api_client.vms.get, vm_name)

    def stop_vm(self, api_client, focal_vm, polling_for):
        vm_name = focal_vm['metadata']['name']
        code, data = api_client.vms.stop(vm_name)
        assert 204 == code, f"Fail to stop VM\n{code}, {data}"
        polling_for("VM do stopped",
                    lambda c, d: 404 == c,
                    api_client.vms.get_status, vm_name)

    def delete_vm(self, api_client, focal_vm, polling_for):
        vm_name = focal_vm['metadata']['name']
        code, data = api_client.vms.delete(vm_name)
        assert 200 == code, f"Fail to delete VM\n{code}, {data}"
        polling_for("VM do deleted",
                    lambda c, d: 404 == c,
                    api_client.vms.get, vm_name)

    def test_delete_volume_bounded_on_existing_vm(self, api_client, focal_vm, polling_for):
        """
        1. Create a VM with volume
        2. Delete volume should reply 422
        3. Pause VM
        4. Delete volume should reply 422 too
        5. Stop VM
        6. Delete volume should reply 422 too
        Ref. https://github.com/harvester/tests/issues/905
        """
        vol_name = (focal_vm["spec"]["template"]["spec"]["volumes"][0]
                            ['persistentVolumeClaim']['claimName'])

        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        self.pause_vm(api_client, focal_vm, polling_for)
        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        self.stop_vm(api_client, focal_vm, polling_for)
        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

    def test_delete_volume_bounded_on_deleted_vm(self, api_client, focal_vm, polling_for):
        """
        1. Create a VM with volume
        2. Delete volume should reply 422
        3. Delete VM but not volume
        4. Delete volume should reply 200
        Ref. https://github.com/harvester/tests/issues/652
        """
        vol_name = (focal_vm["spec"]["template"]["spec"]["volumes"][0]
                            ['persistentVolumeClaim']['claimName'])

        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        self.delete_vm(api_client, focal_vm, polling_for)

        code, data = api_client.volumes.delete(vol_name)
        assert 200 == code, f"Fail to delete volume\n{code}, {data}"
