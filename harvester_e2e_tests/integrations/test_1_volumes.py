import yaml
import pytest
from hashlib import sha512

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.virtualmachines"
]


@pytest.fixture(scope="module")
def ubuntu_image(api_client, unique_name, image_ubuntu, image_checker):
    """
    Generates a Ubuntu image

    1. Creates an image name based on unique_name
    2. Create the image based on URL
    3. Response for creation should be 201
    4. Loop while waiting for image to be created
    5. Yield the image with the namespace and name
    6. Delete the image
    7. The response for getting the image name should be 404 after deletion
    """
    image_name = f"img-{unique_name}"
    code, data = api_client.images.create_by_url(image_name, image_ubuntu.url,
                                                 image_ubuntu.image_checksum)
    assert 201 == code, f"Fail to create image\n{code}, {data}"
    image_created, (code, data) = image_checker.wait_downloaded(image_name)
    assert image_created, (code, data)

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user=image_ubuntu.ssh_user, id=f"{namespace}/{name}", display_name=image_name)

    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        assert 200 == code, f"Fail to cleanup image\n{code}, {data}"
        image_deleted, (code, data) = image_checker.wait_deleted(image_name)
        assert image_deleted, (code, data)


@pytest.fixture(scope="module")
def ubuntu_image_bad_checksum(api_client, unique_name, image_ubuntu, image_checker):
    """
    Generates a Ubuntu image with a bad sha512 checksum

    1. Creates an image name based on unique_name
    2. Create the image based on URL with a bad statically assigned checksum
    3. Response for creation should be 201
    4. Loop while waiting for image to be created
    5. Yield the image with the namespace and name
    6. Delete the image
    7. The response for getting the image name should be 404 after deletion
    """

    image_name = f"img-{unique_name + '-badchecksum'}"
    # Random fake checksum to use in test
    fake_checksum = sha512(b'not_a_valid_checksum').hexdigest()
    code, data = api_client.images.create_by_url(image_name, image_ubuntu.url, fake_checksum)
    assert 201 == code, f"Fail to create image\n{code}, {data}"
    image_created, (code, data) = image_checker.wait_downloaded(image_name)
    assert image_created, (code, data)

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user=image_ubuntu.ssh_user, id=f"{namespace}/{name}", display_name=image_name)
    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        assert 200 == code, f"Fail to cleanup image\n{code}, {data}"
        image_deleted, (code, data) = image_checker.wait_deleted(image_name)
        assert image_deleted, (code, data)


@pytest.fixture(scope="class")
def ubuntu_vm(api_client, unique_name, ubuntu_image, vm_checker, volume_checker):
    vm_name = f"vm-{unique_name}"

    vm_spec = api_client.vms.Spec(1, 2)
    vm_spec.add_image(vm_name, ubuntu_image["id"])
    code, data = api_client.vms.create(vm_name, vm_spec)
    assert 201 == code, f"Fail to create VM\n{code}, {data}"
    vm_running, (code, data) = vm_checker.wait_status_running(vm_name)
    assert vm_running, (code, data)

    volumes = list(filter(lambda vol: "persistentVolumeClaim" in vol,
                          data["spec"]["template"]["spec"]["volumes"]))
    assert len(volumes) == 1

    yield data

    # teardown
    _ = vm_checker.wait_deleted(vm_name)
    vol_name = volumes[0]['persistentVolumeClaim']['claimName']
    code, data = api_client.volumes.get(vol_name)
    if 200 == code:
        code, data = api_client.volumes.delete(vol_name)
        assert 200 == code, f"Fail to cleanup volume\n{code}, {data}"
        volume_deleted, (code, data) = volume_checker.wait_volume_deleted(vol_name)
        assert volume_deleted, (code, data)


@pytest.fixture()
def unique_volume(api_client, unique_name, volume_checker):
    yield unique_name

    code, data = api_client.volumes.delete(unique_name)
    assert 200 == code, (code, data)
    volume_deleted, (code, data) = volume_checker.wait_volume_deleted(unique_name)
    assert volume_deleted, (code, data)


@pytest.mark.p0
@pytest.mark.volumes
@pytest.mark.parametrize("create_as", ["json", "yaml"])
@pytest.mark.parametrize("source_type", ["New", "VM Image"])
def test_create_volume(
    api_client, unique_volume, ubuntu_image, create_as, source_type, polling_for
):
    """
    1. Create a volume from image
    2. Create should respond with 201
    3. Wait for volume to create
    4. Failures should be at 0
    5. Get volume metadata
    6. Volume should not be in error or transitioning state
    7. ImageId should match what was used in create
    8. Delete volume
    9. Delete volume should reply 404 after delete
    Ref.
    """
    image_id, storage_cls = None, None
    if source_type == "VM Image":
        image_id, storage_cls = ubuntu_image['id'], f"longhorn-{ubuntu_image['display_name']}"

    spec = api_client.volumes.Spec("10Gi", storage_cls)
    if create_as == 'yaml':
        kws = dict(headers={'Content-Type': 'application/yaml'}, json=None,
                   data=yaml.dump(spec.to_dict(unique_volume, 'default', image_id=image_id)))
    else:
        kws = dict()
    code, data = api_client.volumes.create(unique_volume, spec, image_id=image_id, **kws)
    assert 201 == code, (code, unique_volume, data, image_id)

    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_volume)
    code2, data2 = api_client.images.get(ubuntu_image['display_name'])
    # This grabs the failed count for the image
    failed: int = data2['status']['failed']
    # This makes sure that the failures are 0
    assert failed <= 3, 'Image failed more than 3 times'

    code, data = api_client.volumes.get(unique_volume)
    mdata, annotations = data['metadata'], data['metadata']['annotations']
    assert 200 == code, (code, data)
    assert unique_volume == mdata['name'], (code, data)
    # status
    assert not mdata['state']['error'], (code, data)
    assert not mdata['state']['transitioning'], (code, data)
    assert data['status']['phase'] == "Bound", (code, data)
    # source
    if source_type == "VM Image":
        assert image_id == annotations['harvesterhci.io/imageId'], (code, data)
    else:
        assert not annotations.get('harvesterhci.io/imageId'), (code, data)


@pytest.mark.p1
@pytest.mark.volumes
@pytest.mark.negative
@pytest.mark.parametrize("create_as", ["json", "yaml"])
@pytest.mark.parametrize("source_type", ["New", "VM Image"])
def test_create_volume_bad_checksum(api_client, unique_volume, ubuntu_image_bad_checksum,
                                    create_as, source_type, polling_for):
    """
    1. Create a volume from image with a bad checksum
    2. Create should respond with 201
    3. Wait for volume to create
    4. Wait for 4 failures in the volume fail status
    5. Failures should be set at 4
    6. Delete volume
    7. Delete volume should reply 404 after delete
    Ref. https://github.com/harvester/tests/issues/1121
    """
    image_id, storage_cls = None, None
    if source_type == "VM Image":
        image_id, storage_cls = ubuntu_image_bad_checksum['id'], \
            f"longhorn-{ubuntu_image_bad_checksum['display_name']}"

    spec = api_client.volumes.Spec("10Gi", storage_cls)
    if create_as == 'yaml':
        kws = dict(headers={'Content-Type': 'application/yaml'}, json=None,
                   data=yaml.dump(spec.to_dict(unique_volume, 'default', image_id=image_id)))
    else:
        kws = dict()
    code, data = api_client.volumes.create(unique_volume, spec, image_id=image_id, **kws)
    assert 201 == code, (code, unique_volume, data, image_id)

    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_volume)
    code2, data2 = api_client.images.get(ubuntu_image_bad_checksum['display_name'])
    polling_for("failed to process sync file",
                lambda code2, data2: 200 == code2 and data2['status']['failed'] == 4,
                api_client.images.get, ubuntu_image_bad_checksum['display_name'])

    # This grabs the failed count for the image
    code2, data2 = api_client.images.get(ubuntu_image_bad_checksum['display_name'])
    failed: int = data2['status']['failed']
    # This makes sure that the tests fails with bad checksum
    assert failed == 4, 'Image download correctly failed more than 3 times with bad checksum'


@pytest.mark.p0
@pytest.mark.volumes
class TestVolumeWithVM:
    def pause_vm(self, api_client, ubuntu_vm, polling_for):
        vm_name = ubuntu_vm['metadata']['name']
        code, data = api_client.vms.pause(vm_name)
        assert 204 == code, f"Fail to pause VM\n{code}, {data}"
        polling_for("VM do paused",
                    lambda c, d: d.get('status', {}).get('printableStatus') == "Paused",
                    api_client.vms.get, vm_name)

    def stop_vm(self, api_client, ubuntu_vm, polling_for):
        vm_name = ubuntu_vm['metadata']['name']
        code, data = api_client.vms.stop(vm_name)
        assert 204 == code, f"Fail to stop VM\n{code}, {data}"
        polling_for("VM do stopped",
                    lambda c, d: 404 == c,
                    api_client.vms.get_status, vm_name)

    def delete_vm(self, api_client, ubuntu_vm, polling_for):
        vm_name = ubuntu_vm['metadata']['name']
        code, data = api_client.vms.delete(vm_name)
        assert 200 == code, f"Fail to delete VM\n{code}, {data}"
        polling_for("VM do deleted",
                    lambda c, d: 404 == c,
                    api_client.vms.get, vm_name)

    def test_delete_volume_on_existing_vm(self, api_client, ubuntu_image, ubuntu_vm, polling_for):
        """
        1. Create a VM with volume
        2. Delete volume should reply 422
        3. Pause VM
        4. Delete volume should reply 422 too
        5. Stop VM
        6. Delete volume should reply 422 too
        Ref. https://github.com/harvester/tests/issues/905
        """
        vol_name = (ubuntu_vm["spec"]["template"]["spec"]["volumes"][0]
                             ['persistentVolumeClaim']['claimName'])

        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        self.pause_vm(api_client, ubuntu_vm, polling_for)
        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        self.stop_vm(api_client, ubuntu_vm, polling_for)
        code, data = api_client.volumes.delete(vol_name)
        assert 422 == code, f"Should fail to delete volume\n{code}, {data}"

        # Check Volume
        code, data = api_client.volumes.get(vol_name)
        mdata, annotations = data['metadata'], data['metadata']['annotations']
        assert 200 == code, (code, data)
        assert mdata['name'] == vol_name, (code, data)
        # status
        assert not mdata['state']['error'], (code, data)
        assert not mdata['state']['transitioning'], (code, data)
        assert data['status']['phase'] == "Bound", (code, data)
        # source
        assert ubuntu_image["id"] == annotations['harvesterhci.io/imageId'], (code, data)

    def test_delete_volume_on_deleted_vm(self, api_client, ubuntu_image, ubuntu_vm, polling_for):
        """
        1. Create a VM with volume
        2. Delete VM but not volume
        3. Delete volume concurrently with VM
        4. VM should be deleted
        5. Volume should be deleted
        Ref. https://github.com/harvester/tests/issues/652
        """
        vm_name = ubuntu_vm['metadata']['name']
        vol_name = (ubuntu_vm["spec"]["template"]["spec"]["volumes"][0]
                             ['persistentVolumeClaim']['claimName'])

        api_client.vms.delete(vm_name)

        polling_for("Delete volume",
                    lambda c, d: 200 == c,
                    api_client.volumes.delete, vol_name)

        # Retry since VM is deleting
        polling_for("VM do deleted",
                    lambda c, d: 404 == c,
                    api_client.vms.get, vm_name)
        polling_for("Volume do deleted",
                    lambda c, d: 404 == c,
                    api_client.volumes.get, vol_name)
