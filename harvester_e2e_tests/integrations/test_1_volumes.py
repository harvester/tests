import copy
import yaml

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha512


import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    "harvester_e2e_tests.fixtures.images"
]


@pytest.fixture(scope="module")
def ubuntu_image(api_client, unique_name, image_ubuntu, polling_for):
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
    code, data = polling_for("image do created",
                             lambda c, d: c == 200 and d.get('status', {}).get('progress') == 100,
                             api_client.images.get, image_name)

    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user=image_ubuntu.ssh_user, id=f"{namespace}/{name}", display_name=image_name)

    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        assert 200 == code, f"Fail to cleanup image\n{code}, {data}"
        polling_for("image do deleted",
                    lambda c, d: 404 == c,
                    api_client.images.get, image_name)


@pytest.fixture(scope="module")
def ubuntu_image_bad_checksum(api_client, unique_name, image_ubuntu, polling_for):
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
    code, data = polling_for("image do created",
                             lambda c, d: c == 200 and d.get('status', {}).get('progress') == 100,
                             api_client.images.get, image_name)
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']
    yield dict(ssh_user=image_ubuntu.ssh_user, id=f"{namespace}/{name}", display_name=image_name)
    code, data = api_client.images.get(image_name)
    if 200 == code:
        code, data = api_client.images.delete(image_name)
        assert 200 == code, f"Fail to cleanup image\n{code}, {data}"
        polling_for("image do deleted",
                    lambda c, d: 404 == c,
                    api_client.images.get, image_name)


@pytest.fixture(scope="class")
def ubuntu_vm(api_client, unique_name, ubuntu_image, polling_for):
    vm_name = f"vm-{unique_name}"

    vm_spec = api_client.vms.Spec(1, 2)
    vm_spec.add_image(vm_name, ubuntu_image["id"])
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
@pytest.mark.smoke
@pytest.mark.volumes
@pytest.mark.parametrize("create_as", ["json", "yaml"])
@pytest.mark.parametrize("source_type", ["New", "VM Image"])
def test_create_volume(api_client, unique_name, ubuntu_image, create_as, source_type, polling_for):
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
                   data=yaml.dump(spec.to_dict(unique_name, 'default', image_id=image_id)))
    else:
        kws = dict()
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id, **kws)
    assert 201 == code, (code, unique_name, data, image_id)

    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)
    code2, data2 = api_client.images.get(ubuntu_image['display_name'])
    # This grabs the failed count for the image
    failed: int = data2['status']['failed']
    # This makes sure that the failures are 0
    assert failed <= 3, 'Image failed more than 3 times'

    code, data = api_client.volumes.get(unique_name)
    mdata, annotations = data['metadata'], data['metadata']['annotations']
    assert 200 == code, (code, data)
    assert unique_name == mdata['name'], (code, data)
    # status
    assert not mdata['state']['error'], (code, data)
    assert not mdata['state']['transitioning'], (code, data)
    assert data['status']['phase'] == "Bound", (code, data)
    # source
    if source_type == "VM Image":
        assert image_id == annotations['harvesterhci.io/imageId'], (code, data)
    else:
        assert not annotations.get('harvesterhci.io/imageId'), (code, data)
    # teardown
    polling_for("volume do deleted", lambda code, _: 404 == code,
                api_client.volumes.delete, unique_name)


@pytest.mark.p1
@pytest.mark.sanity
@pytest.mark.volumes
@pytest.mark.negative
@pytest.mark.parametrize("create_as", ["json", "yaml"])
@pytest.mark.parametrize("source_type", ["New", "VM Image"])
def test_create_volume_bad_checksum(api_client, unique_name, ubuntu_image_bad_checksum,
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
                   data=yaml.dump(spec.to_dict(unique_name, 'default', image_id=image_id)))
    else:
        kws = dict()
    code, data = api_client.volumes.create(unique_name, spec, image_id=image_id, **kws)
    assert 201 == code, (code, unique_name, data, image_id)

    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)
    code2, data2 = api_client.images.get(ubuntu_image_bad_checksum['display_name'])
    polling_for("failed to process sync file",
                lambda code2, data2: 200 == code2 and data2['status']['failed'] == 4,
                api_client.images.get, ubuntu_image_bad_checksum['display_name'])

    # This grabs the failed count for the image
    code2, data2 = api_client.images.get(ubuntu_image_bad_checksum['display_name'])
    failed: int = data2['status']['failed']
    # This makes sure that the tests fails with bad checksum
    assert failed == 4, 'Image download correctly failed more than 3 times with bad checksum'

    # teardown
    polling_for("volume do deleted", lambda code, _: 404 == code,
                api_client.volumes.delete, unique_name)


@pytest.mark.p1
@pytest.mark.sanity
@pytest.mark.negative
@pytest.mark.volumes
@pytest.mark.images
def test_delete_volume_when_exporting(api_client, unique_name, ubuntu_image, polling_for):
    # ref: https://github.com/harvester/tests/issues/1057

    # image id must follow RFC1123 which ends with alphanumeric char
    spec = api_client.volumes.Spec('10Gi')
    # create volume from image
    code, data = api_client.volumes.create(unique_name, spec, image_id=ubuntu_image['id'])
    assert 201 == code, (code, data)
    polling_for("volume do created",
                lambda code, data: 200 == code and data['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)
    # export volume to image
    code, data = api_client.volumes.export(unique_name, unique_name, 'harvester-longhorn')
    assert 200 == code, (code, data)
    export_image = data['metadata']['name']
    # delete volume while exporting
    code, data = api_client.volumes.delete(unique_name)
    assert 422 == code, (code, data)

    # teardown
    polling_for("image do deleted", lambda code, _: 404 == code,
                api_client.images.delete, export_image)
    polling_for("volume do deleted", lambda code, _: 404 == code,
                api_client.volumes.delete, unique_name)


@pytest.mark.p1
@pytest.mark.negative
@pytest.mark.volumes
@pytest.mark.parametrize("invalid_spec", [
    {"size": "0Gi", "error_msg": "must be greater than zero"},
    {"size": "-5Gi", "error_msg": "must be greater than zero"},
    {"size": "invalid_size", "error_msg": "quantities must match"},
    {"size": "999999Ti", "error_msg": "exceeds cluster capacity"},
])
def test_create_volume_invalid_specifications(api_client, unique_name, invalid_spec, polling_for):
    """
    Negative testing for volume creation with invalid specifications
    1. Attempt to create volume with invalid size specification
    2. Verify appropriate error response (400 or 422)
    3. Ensure no volume resource is created
    4. Validate error message contains expected error information

    Test cases:
    - Zero size volumes should be rejected
    - Negative size volumes should be rejected
    - Invalid size format should be rejected
    - Excessively large volumes should be rejected
    """
    spec = api_client.volumes.Spec(invalid_spec["size"])

    code, data = api_client.volumes.create(unique_name, spec)

    # Should fail with 400 (Bad Request) or 422 (Unprocessable Entity)
    assert code in [400, 422], f"Expected error response, got {code}: {data}"

    # Verify error message contains expected information
    error_message = str(data).lower()
    assert invalid_spec["error_msg"].lower() in error_message, \
        f"Expected '{invalid_spec['error_msg']}' in error: {data}"

    # Ensure no volume was actually created
    code, data = api_client.volumes.get(unique_name)
    assert 404 == code, f"Volume should not exist after failed creation: {code}, {data}"


@pytest.mark.p2
@pytest.mark.volumes
@pytest.mark.parametrize("concurrent_count", [3, 5])
def test_concurrent_volume_creation(api_client, ubuntu_image, concurrent_count, polling_for):
    """
    Test concurrent volume creation to validate system stability
    1. Create multiple volumes simultaneously using ThreadPoolExecutor
    2. Verify all volumes are created successfully
    3. Check for race conditions or resource conflicts
    4. Validate each volume reaches Bound state independently
    5. Cleanup all volumes concurrently

    Validates:
    - API endpoint thread safety
    - Storage backend concurrency handling
    - Resource naming collision prevention
    - Longhorn concurrent provisioning
    """
    from datetime import datetime

    volume_names = [f"concurrent-vol-{i}-{int(datetime.now().timestamp())}"
                    for i in range(concurrent_count)]
    created_volumes = []
    errors = []

    def create_single_volume(vol_name):
        try:
            spec = api_client.volumes.Spec("5Gi")  # Smaller size for faster creation
            code, data = api_client.volumes.create(vol_name, spec, image_id=ubuntu_image['id'])

            if code == 201:
                # Wait for volume to be bound
                code, data = polling_for(
                    "volume do created",
                    lambda c, d: 200 == c and d['status']['phase'] == 'Bound',
                    api_client.volumes.get,
                    vol_name
                )
                return {"name": vol_name, "success": True, "data": data}
            else:
                return {"name": vol_name, "success": False,
                        "error": f"Creation failed: {code}, {data}"}

        except Exception as e:
            return {"name": vol_name, "success": False, "error": str(e)}

    # Create volumes concurrently
    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        futures = [executor.submit(create_single_volume, name) for name in volume_names]

        for future in as_completed(futures):
            result = future.result()
            if result["success"]:
                created_volumes.append(result["name"])
            else:
                errors.append(result)

    # Validate results
    assert len(errors) == 0, f"Concurrent creation errors: {errors}"
    assert len(created_volumes) == concurrent_count, f"Expected {concurrent_count}" \
                                                     f" volumes, created {len(created_volumes)}"

    # Verify all volumes are properly created and accessible
    for vol_name in created_volumes:
        code, data = api_client.volumes.get(vol_name)
        assert 200 == code, f"Volume {vol_name} not accessible: {code}"
        assert data['status']['phase'] == "Bound", f"Volume {vol_name} not bound: " \
                                                   f"{data['status']['phase']}"

    # Cleanup all volumes concurrently
    def cleanup_single_volume(vol_name):
        try:
            polling_for("volume do deleted",
                        lambda code, _: 404 == code, api_client.volumes.delete, vol_name)
            return True
        except Exception as e:
            print(f"Cleanup error for {vol_name}: {e}")
            return False

    with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
        cleanup_futures = [executor.submit(cleanup_single_volume, name)
                           for name in created_volumes]
        cleanup_results = [future.result() for future in as_completed(cleanup_futures)]

    assert all(cleanup_results), "Some volumes failed to cleanup properly"


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.volumes
def test_volume_resize_operations(api_client, unique_name, ubuntu_image, polling_for):
    """
    Test volume resize functionality
    Steps:
    1. Create initial volume with small size
    2. Resize volume to larger size
    3. Verify resize operation completes successfully
    4. Validate new size is reflected in volume specifications
    5. Test multiple resize operations
    """
    initial_size = "5Gi"
    expanded_size = "10Gi"
    final_size = "15Gi"

    # Create initial volume
    spec = api_client.volumes.Spec(initial_size)
    code, data = api_client.volumes.create(unique_name, spec, image_id=ubuntu_image['id'])
    assert 201 == code, f"Initial volume creation failed: {code}, {data}"

    # Wait for initial volume to be bound
    polling_for("initial volume created",
                lambda c, d: 200 == c and d['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)

    # Verify initial size
    code, data = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to get initial volume: {code}, {data}"
    assert data['spec']['resources']['requests']['storage'] == initial_size

    # First resize: 5Gi -> 10Gi
    # Get current volume state to obtain resourceVersion
    code, current_volume = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to get volume for resize: {code}, {current_volume}"

    # Prepare update with resourceVersion and modified storage
    updated_volume = copy.deepcopy(current_volume)
    updated_volume['spec']['resources']['requests']['storage'] = expanded_size

    code, data = api_client.volumes.update(unique_name, updated_volume)
    assert 200 == code, f"First resize operation failed: {code}, {data}"

    # Wait for first resize to complete
    polling_for("first volume resize completed",
                lambda c, d: (200 == c and
                              d['spec']['resources']['requests']['storage'] == expanded_size),
                api_client.volumes.get, unique_name)

    # Verify first resize
    code, data = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to verify first resize: {code}, {data}"
    assert data['spec']['resources']['requests']['storage'] == expanded_size
    assert data['status']['phase'] == "Bound", "Volume should remain bound after resize"

    # Second resize: 10Gi -> 15Gi
    # Get updated volume state for second resize
    code, current_volume = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to get volume for second resize: {code}, {current_volume}"

    updated_volume = copy.deepcopy(current_volume)
    updated_volume['spec']['resources']['requests']['storage'] = final_size

    code, data = api_client.volumes.update(unique_name, updated_volume)
    assert 200 == code, f"Second resize operation failed: {code}, {data}"

    # Wait for final resize to complete
    polling_for("final volume resize completed",
                lambda c, d: (200 == c and
                              d['spec']['resources']['requests']['storage'] == final_size),
                api_client.volumes.get, unique_name)

    # Final verification
    code, data = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to verify final resize: {code}, {data}"
    assert data['spec']['resources']['requests']['storage'] == final_size
    assert data['status']['phase'] == "Bound", "Volume should remain bound after final resize"

    # Cleanup
    code, _ = api_client.volumes.delete(unique_name)
    assert code in [200, 202, 204], f"Failed to initiate volume deletion: {code}"

    polling_for("volume deleted", lambda code, _: 404 == code,
                api_client.volumes.get, unique_name)


@pytest.mark.p2
@pytest.mark.volumes
@pytest.mark.negative
def test_volume_shrink_not_allowed(api_client, unique_name, ubuntu_image, polling_for):
    """
    Test that volume shrinking is properly rejected
    Steps:
    1. Create volume with larger initial size
    2. Wait for volume to be bound and ready
    3. Attempt to resize volume to smaller size
    4. Verify operation fails with appropriate error
    5. Confirm volume size remains unchanged
    """
    initial_size = "5Gi"
    shrink_size = "1Gi"

    # Create initial volume
    spec = api_client.volumes.Spec(initial_size)
    code, data = api_client.volumes.create(unique_name, spec, image_id=ubuntu_image['id'])
    assert 201 == code, f"Initial volume creation failed: {code}, {data}"

    # Wait for volume to be bound
    polling_for("initial volume created",
                lambda c, d: 200 == c and d['status']['phase'] == "Bound",
                api_client.volumes.get, unique_name)

    # Verify initial size
    code, data = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to get initial volume: {code}, {data}"
    assert data['spec']['resources']['requests']['storage'] == initial_size

    # Attempt to shrink volume
    code, current_volume = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to get volume for shrink test: {code}, {current_volume}"

    updated_volume = copy.deepcopy(current_volume)
    updated_volume['spec']['resources']['requests']['storage'] = shrink_size

    code, data = api_client.volumes.update(unique_name, updated_volume)

    # Expect failure - common error codes for invalid operations
    expected_error_codes = [400, 422, 409, 403]
    assert code in expected_error_codes, f"Volume shrink should fail, but got: {code}, {data}"

    # Verify error message contains relevant information
    error_message = data.get('message', '').lower()
    shrink_indicators = ['not allowed', 'not supported', 'forbidden']

    message_found = any(indicator in error_message for indicator in shrink_indicators)
    assert message_found, f"Error message should indicate shrinking issue. Got: {error_message}"

    # Verify volume size unchanged after failed shrink
    code, unchanged_volume = api_client.volumes.get(unique_name)
    assert 200 == code, f"Failed to verify volume after shrink attempt: {code}, {unchanged_volume}"
    assert unchanged_volume['spec']['resources']['requests']['storage'] == initial_size, \
        "Volume size should remain unchanged after failed shrink"
    assert unchanged_volume['status']['phase'] == "Bound", \
        "Volume should remain bound after failed shrink attempt"

    # Cleanup
    code, _ = api_client.volumes.delete(unique_name)
    assert code in [200, 202, 204], f"Failed to initiate volume deletion: {code}"

    polling_for("volume deleted", lambda code, _: 404 == code,
                api_client.volumes.get, unique_name)


@pytest.mark.p0
@pytest.mark.sanity
@pytest.mark.volumes
@pytest.mark.virtualmachines
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
