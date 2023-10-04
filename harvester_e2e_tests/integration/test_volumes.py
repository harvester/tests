from urllib.parse import urljoin

import yaml
import pytest

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
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
    yield dict(ssh_user="ubuntu", id=f"{namespace}/{name}", display_name=image_name)

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


@pytest.mark.p0
@pytest.mark.volumes
@pytest.mark.parametrize("create_as", ["json", "yaml"])
def test_create_volume_backing_image(api_client, unique_name, polling_for, focal_image, create_as):
    """
    1. Create a new image from URL
    2. Check that it is created succesffully.
    3. Create a new volume with the image_id of the previous image
    4. Check that the new image is created
    5. Delete image and volume
    """
    image_id, display_name = focal_image['id'], focal_image['display_name']

    spec = api_client.volumes.Spec("10Gi", f"longhorn-{display_name}")
    if create_as == 'yaml':
        kws = dict(headers={'Content-Type': 'application/yaml'}, json=None,
                   data=yaml.dump(spec.to_dict(unique_name, 'default', image_id=image_id)))
    else:
        kws = dict()
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id, **kws)
    assert 201 == code, (code, unique_name, data, image_id)

    # Verify: volume created & bounded & based on image & name is correct
    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)
    code, data = api_client.volumes.get(unique_name)
    assert 200 == code, (code, data)
    assert data['status']['phase'] == "Bound", (data)
    assert image_id == data['metadata']['annotations']['harvesterhci.io/imageId']
    assert unique_name == data['metadata']['name'], (code, data)

    # teardown
    polling_for("volume do deleted", lambda code, _: 404 == code,
                api_client.volumes.delete, unique_name)


@pytest.mark.p0
@pytest.mark.volumes
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
