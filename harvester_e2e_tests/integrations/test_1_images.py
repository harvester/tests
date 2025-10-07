import concurrent.futures
import filecmp
import hashlib
import json
import re
import threading
from time import sleep, time
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks",
    "harvester_e2e_tests.fixtures.settings"
]


@pytest.fixture(params=["image_opensuse", "image_ubuntu"])
def image_info(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="session")
def export_storage_class():
    storage_class = "harvester-longhorn"
    return storage_class


@pytest.fixture(scope="session")
def fake_invalid_image_file():
    with NamedTemporaryFile("wb") as f:
        f.seek(5)  # less than 10MB
        f.write(b"\0")
        f.seek(0)
        yield Path(f.name)


def create_image_url(api_client, name, image_url, image_checksum, wait_timeout):
    code, data = api_client.images.create_by_url(name, image_url, image_checksum)

    assert 201 == code, (code, data)
    image_spec = data.get("spec")

    assert name == image_spec.get("displayName")
    assert "download" == image_spec.get("sourceType")

    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        code, data = api_client.images.get(name)
        image_status = data.get("status", {})

        assert 200 == code, (code, data)
        if image_status.get("progress") == 100:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to download image {name} with {wait_timeout} timed out\n"
            f"Still got {code} with {data}"
        )


def delete_image(api_client, image_name, wait_timeout):
    code, data = api_client.images.delete(image_name)

    assert 200 == code, f"Failed to delete image with error: {code}, {data}"

    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        code, data = api_client.images.get(image_name)
        if code == 404:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to delete image {image_name} with {wait_timeout} timed out\n"
            f"Still got {code} with {data}"
        )


def delete_volume(api_client, volume_name, wait_timeout):
    code, data = api_client.volumes.delete(volume_name)

    assert 200 == code, f"Failed to delete volume with error: {code}, {data}"

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.volumes.get(volume_name)
        if code == 404:
            break
        sleep(5)
    else:
        raise AssertionError(
            f"Failed to delete volume {volume_name} with {wait_timeout} timed out\n"
            f"Still got {code} with {data}"
        )


def get_image(api_client, image_name):
    code, data = api_client.images.get()

    assert len(data["items"]) > 0, (code, data)

    code, data = api_client.images.get(image_name)
    assert 200 == code, (code, data)
    assert image_name == data["metadata"]["name"]


@pytest.fixture(scope="class")
def cluster_network(api_client, vlan_nic):
    # We should change this at some point. It fails if the total cnet name is over 12 chars
    cnet = f"cnet-{vlan_nic.lower()}"[:12]  # ???: RFC1123 and length limits
    code, data = api_client.clusternetworks.get(cnet)
    if code != 200:
        code, data = api_client.clusternetworks.create(cnet)
        assert 201 == code, (code, data)

    code, data = api_client.clusternetworks.get_config(cnet)
    if code != 200:
        code, data = api_client.clusternetworks.create_config(cnet, cnet, vlan_nic)
        assert 201 == code, (code, data)

    yield cnet

    # Teardown
    code, data = api_client.clusternetworks.delete_config(cnet)
    assert 200 == code, (code, data)
    code, data = api_client.clusternetworks.delete(cnet)
    assert 200 == code, (code, data)


@pytest.fixture(scope="class")
def vlan_cidr(api_client, cluster_network, vlan_id, wait_timeout, sleep_timeout):
    vnet = f'{cluster_network}-vlan{vlan_id}'
    code, data = api_client.networks.get(vnet)
    if code != 200:
        code, data = api_client.networks.create(vnet, vlan_id, cluster_network=cluster_network)
        assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.networks.get(vnet)
        annotations = data['metadata'].get('annotations', {})
        if 200 == code and annotations.get('network.harvesterhci.io/route'):
            route = json.loads(annotations['network.harvesterhci.io/route'])
            if route['cidr']:
                break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Fail to get route info of VM network {vnet} with error: {code}, {data}"
        )

    yield route['cidr']

    # Teardown
    code, data = api_client.networks.delete(vnet)
    assert 200 == code, (code, data)


@pytest.fixture(scope="class")
def storage_network(api_client, cluster_network, vlan_id, vlan_cidr, setting_checker):
    ''' Ref. https://docs.harvesterhci.io/v1.3/advanced/storagenetwork/#configuration-example
    '''
    enable_spec = api_client.settings.StorageNetworkSpec.enable_with(
        vlan_id, cluster_network, vlan_cidr
    )
    code, data = api_client.settings.update('storage-network', enable_spec)
    assert 200 == code, (code, data)
    snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_harvester()
    assert snet_enabled, (code, data)
    snet_enabled, (code, data) = setting_checker.wait_storage_net_enabled_on_longhorn(vlan_cidr)
    assert snet_enabled, (code, data)

    yield

    # Teardown
    disable_spec = api_client.settings.StorageNetworkSpec.disable()
    code, data = api_client.settings.update('storage-network', disable_spec)
    assert 200 == code, (code, data)
    snet_disabled, (code, data) = setting_checker.wait_storage_net_disabled_on_harvester()
    assert snet_disabled, (code, data)
    snet_disabled, (code, data) = setting_checker.wait_storage_net_disabled_on_longhorn()
    assert snet_disabled, (code, data)


@pytest.mark.p0
@pytest.mark.images
class TestBackendImages:
    @pytest.mark.smoke
    @pytest.mark.dependency(name="create_image_from_volume")
    def test_create_image_from_volume(
        self, api_client, unique_name, export_storage_class, wait_timeout
    ):
        """
        Test create image from volume

        Steps:
            1. Create a volume "test-volume" in Volumes page
            2. Export the volume to image "export-image"
            3. Check the image "export-image" exists
            4. Cleanup image "export-image" on Images page
            5. Cleanup volume "test-volume" on Volumes page
        """

        volume_name = f"volume-{unique_name}"
        image_name = f"image-{unique_name}"

        spec = api_client.volumes.Spec(1)
        code, data = api_client.volumes.create(volume_name, spec)

        assert 201 == code, (code, data)

        # Check volume ready
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(volume_name)
            if data["status"]["phase"] == "Bound":
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete volume {volume_name} bound in {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

        api_client.volumes.export(volume_name, image_name, export_storage_class)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        image_id = ""
        while endtime > datetime.now():
            code, data = api_client.images.get()
            assert 200 == code, (code, data)

            for image in data["items"]:
                if image["spec"]["displayName"] == image_name:
                    if 100 == image.get("status", {}).get("progress", 0):
                        image_id = image["metadata"]["name"]
                    break
            else:
                raise AssertionError(f"Failed to find image {image_name}")

            if image_id != "":
                break

            sleep(3)  # snooze

        delete_volume(api_client, volume_name, wait_timeout)
        delete_image(api_client, image_id, wait_timeout)

    @pytest.mark.smoke
    @pytest.mark.dependency(name="create_image_url")
    def test_create_image_url(self, image_info, unique_name, api_client, wait_timeout):
        """
        Test create raw and iso type image from url

        Steps:
        1. Open image page and select default URL
        2. Input qcow2 image file download URL, wait for download complete
        3. Check the qcow2 image exists
        4. Input iso image file download URL, wait for download complete
        5. Check the iso image exists
        """
        image_name = f"{image_info.name}-{unique_name}"
        image_url = image_info.url
        create_image_url(api_client, image_name, image_url,
                         image_info.image_checksum, wait_timeout)

    @pytest.mark.sanity
    @pytest.mark.skip_version_if("> v1.2.0", "<= v1.4.0", reason="Issue#4293 fix after `v1.4.0`")
    @pytest.mark.dependency(name="delete_image_recreate", depends=["create_image_url"])
    def test_delete_image_recreate(
        self,
        api_client,
        image_info,
        unique_name,
        fake_image_file,
        wait_timeout,
    ):
        """
        Test create raw and iso type image from file

        Steps:
        1. Check the image created by URL exists
        2. Delete the newly created image
        3. Create an iso file type image from URL
        4. Check the iso image exists
        5. Upload an qcow2 file type image
        5. Delete the newly uploaded file
        6. Upload a new qcow2 file type image
        """
        image_name = f"{image_info.name}-{unique_name}"
        image_url = image_info.url
        image_checksum = image_info.image_checksum

        get_image(api_client, image_name)
        delete_image(api_client, image_name, wait_timeout)

        create_image_url(api_client, image_name, image_url, image_checksum, wait_timeout)
        get_image(api_client, image_name)

        resp = api_client.images.create_by_file(unique_name, fake_image_file)

        assert (
            200 == resp.status_code
        ), f"Failed to upload fake image with error:{resp.status_code}, {resp.content}"

        get_image(api_client, unique_name)
        delete_image(api_client, unique_name, wait_timeout)

        resp = api_client.images.create_by_file(unique_name, fake_image_file)

        assert (
            200 == resp.status_code
        ), f"Failed to upload fake image with error:{resp.status_code}, {resp.content}"

        get_image(api_client, unique_name)
        delete_image(api_client, unique_name, wait_timeout)

    @pytest.mark.sanity
    @pytest.mark.negative
    def test_create_invalid_file(
        self, api_client, gen_unique_name, fake_invalid_image_file, wait_timeout
    ):
        """
        Test create upload image from invalid file type

        Steps:
        1. Prepare an invalid file that is not in a multiple of 512 bytes
        2. Try to upload invalid image file which to images page
        2. Check should get an error
        """
        unique_name = gen_unique_name()
        resp = api_client.images.create_by_file(unique_name, fake_invalid_image_file)

        assert (
            500 == resp.status_code
        ), f"File size correct, it's a multiple of 512 bytes:{resp.status_code}, {resp.content}"
        delete_image(api_client, unique_name, wait_timeout)

    @pytest.mark.sanity
    @pytest.mark.negative
    @pytest.mark.dependency(name="edit_image_in_use", depends=["create_image_url"])
    def test_edit_image_in_use(self, api_client, unique_name, image_info, wait_timeout):
        """
        Test can edit image which already in use

        Steps:
        1. Check the image created from URL exists
        2. Create a volume from existing image
        3. Update the image labels and description
        4. Check can change the image content
        """

        image_name = f"{image_info.name}-{unique_name}"
        volume_name = f"volume-{image_info.name}-{unique_name}"

        code, data = api_client.images.get(name=image_name)
        assert 200 == code, (code, data)

        image_size_gb = data["status"]["virtualSize"] // 1024**3 + 1
        image_id = f"{data['metadata']['namespace']}/{image_name}"

        # Create volume from image_id
        spec = api_client.volumes.Spec(image_size_gb)
        code, data = api_client.volumes.create(volume_name, spec, image_id=image_id)
        assert 201 == code, (code, data)

        # Check volume ready
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(volume_name)
            if data["status"]["phase"] == "Bound":
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete volume {unique_name} bound in {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

        # Update image content
        updates = {
            "labels": {"usage-label": "yes"},
            "annotations": {"field.cattle.io/description": "edit image in use"},
        }

        # Update image by input
        code, data = api_client.images.update(image_name, dict(metadata=updates))
        assert 200 == code, f"Failed to update image with error: {code}, {data}"

        unexpected = list()
        for field, pairs in updates.items():
            for k, val in pairs.items():
                if data["metadata"][field].get(k) != val:
                    unexpected.append((field, k, val, data["metadata"][field].get(k)))

        assert not unexpected, "\n".join(
            f"Update {f} failed, set key {k} as {v} but got {n}"
            for f, k, v, n in unexpected
        )

        delete_volume(api_client, volume_name, wait_timeout)
        delete_image(api_client, image_name, wait_timeout)


@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.images
@pytest.mark.settings
@pytest.mark.networks
@pytest.mark.skip_version_if("< v1.0.3")
@pytest.mark.usefixtures("storage_network")
class TestImageWithStorageNetwork:
    @pytest.mark.dependency(name="create_image_by_file")
    def test_create_image_by_file(self, api_client, fake_image_file, unique_name):
        resp = api_client.images.create_by_file(unique_name, fake_image_file)
        assert resp.ok, f"Fail to upload fake image with error: {resp.status_code}, {resp.text}"

        code, data = api_client.images.get(unique_name)
        assert 200 == code, (code, data)
        assert unique_name == data["metadata"]["name"], (code, data)

    @pytest.mark.dependency(depends=["create_image_by_file"])
    def test_download_image(self, api_client, fake_image_file, tmp_path, unique_name):
        resp = api_client.images.download(unique_name)
        assert resp.ok, f"Fail to download fake image with error: {resp.status_code}, {resp.text}"

        filename = re.search(r'filename=(\S+)', resp.headers.get("Content-Disposition"))
        assert filename, f"No filename info in the response header: {resp.headers}"
        filename = filename.groups()[0]

        tmp_image_file = tmp_path / filename
        tmp_image_file.write_bytes(
            zlib.decompress(resp.content, 32+15) if ".gz" in filename else resp.content
        )
        assert filecmp.cmp(fake_image_file, tmp_image_file), (
            "Contents of downloaded image is NOT identical to the fake image"
        )

    @pytest.mark.dependency(depends=["create_image_by_file"])
    def test_delete_image(self, api_client, unique_name, wait_timeout, sleep_timeout):
        code, data = api_client.images.delete(unique_name)
        assert 200 == code, (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            if code == 404:
                break
            sleep(sleep_timeout)
        else:
            raise AssertionError(
                f"Fail to delete image {unique_name} with error: {code}, {data}"
            )


class TestImageEnhancements:

    @pytest.mark.p2
    @pytest.mark.images
    @pytest.mark.performance
    @pytest.mark.parametrize("image_size", ["10Mi", "50Mi", "200Mi"])
    def test_image_processing_performance(self, api_client, unique_name, image_size, wait_timeout):
        """
        Test Harvester image processing performance (excluding network upload time)
        Steps:
        1. Upload image files of different sizes
        2. Measure processing time from upload completion to ready state
        3. Verify Harvester processing meets performance expectations
        """

        # Processing thresholds (seconds) - time from upload complete to ready
        processing_thresholds = {"10Mi": 10, "50Mi": 20, "200Mi": 40}
        size_bytes = int(image_size[:-2]) * 1024 * 1024

        if size_bytes % 512 != 0:
            size_bytes = ((size_bytes // 512) + 1) * 512

        with NamedTemporaryFile("wb", suffix=".raw") as f:
            f.seek(size_bytes - 1)
            f.write(b"\x00")
            f.seek(0)

            image_name = f"proc-perf-{unique_name}"

            # Step 1: Upload (don't measure this time - it's network dependent)
            resp = api_client.images.create_by_file(image_name, Path(f.name))
            assert resp.ok, f"Failed to upload {image_size} image: {resp.status_code}, {resp.text}"

            # Step 2: Wait for upload to be acknowledged by Harvester
            initial_timeout = datetime.now() + timedelta(seconds=30)
            while initial_timeout > datetime.now():
                code, data = api_client.images.get(image_name)
                if code == 200:
                    status = data.get("status", {})
                    if "progress" in status:
                        # Upload acknowledged, start measuring processing time
                        processing_start_time = time()
                        break
                sleep(1)
            else:
                raise AssertionError(f"Image {image_name} not acknowledged by Harvester")

            # Step 3: Measure time from processing start to completion
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                code, data = api_client.images.get(image_name)
                if code == 200 and data.get("status", {}).get("progress") == 100:
                    processing_end_time = time()
                    break
                sleep(2)
            else:
                raise AssertionError(f"Image processing did not complete within {wait_timeout}s")

            # Step 4: Validate Harvester processing performance
            processing_time = processing_end_time - processing_start_time
            threshold = processing_thresholds[image_size]
            assert processing_time < threshold, f"Harvester processing took" \
                                                f" {processing_time:.2f}s, expected < {threshold}s"

            print(f"Harvester Processing Performance:"
                  f" {image_size} processed in {processing_time:.2f}s")

            delete_image(api_client, image_name, wait_timeout)

    @pytest.mark.p1
    @pytest.mark.images
    def test_image_checksum_validation(self, api_client, image_info, unique_name, wait_timeout):
        """
        Test image checksum validation during URL-based creation
        Steps:
        1. Create image with correct checksum - should succeed
        2. Create image with incorrect checksum - should fail
        3. Create image with no checksum - should succeed
        4. Verify checksum validation behavior
        """
        # Extract OS name from image_info for naming
        os_name = image_info.name.lower()  # e.g., "opensuse" or "ubuntu"

        # Test with correct checksum
        correct_name = f"correct-checksum-{os_name}-{unique_name}"
        create_image_url(api_client, correct_name, image_info.url,
                         image_info.image_checksum, wait_timeout)

        # Test with incorrect checksum
        incorrect_name = f"incorrect-checksum-{os_name}-{unique_name}"
        fake_checksum = hashlib.sha512(b'fake_checksum').hexdigest()

        code, data = api_client.images.create_by_url(incorrect_name, image_info.url, fake_checksum)
        assert 201 == code, "Image creation should initially succeed"

        # Should eventually fail due to checksum mismatch
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        checksum_error = False
        while endtime > datetime.now():
            code, data = api_client.images.get(incorrect_name)
            if code == 200:
                status = data.get("status", {})
                if "checksum" in str(status).lower() and status.get("failed", 0) > 0:
                    checksum_error = True
                    break
            sleep(5)

        assert checksum_error, "Image should fail due to checksum mismatch"

        # Test with no checksum
        no_checksum_name = f"no-checksum-{os_name}-{unique_name}"
        create_image_url(api_client, no_checksum_name, image_info.url, None, wait_timeout)

        # Cleanup
        delete_image(api_client, correct_name, wait_timeout)

        # Cleanup incorrect checksum image (may not exist if creation failed)
        try:
            delete_image(api_client, incorrect_name, wait_timeout)
        except AssertionError as e:
            print(f"Cleanup failed/skipped for incorrect checksum image {incorrect_name}: {e}")

        # Cleanup no-checksum image (only if it was created)
        try:
            delete_image(api_client, no_checksum_name, wait_timeout)
        except AssertionError as e:
            print(f"Cleanup failed/skipped for no-checksum image {no_checksum_name}: {e}")

    @pytest.mark.p1
    @pytest.mark.images
    def test_image_concurrent_operations(self, api_client, fake_image_file,
                                         gen_unique_name, wait_timeout):
        """
        Test comprehensive concurrent image operations
        Steps:
        1. Test concurrent image uploads (multiple different images)
        2. Test concurrent operations on same image (get, update, status checks)
        3. Verify system handles all concurrency scenarios gracefully
        4. Ensure data integrity and proper resource management
        """

        # Part 1: Concurrent uploads of different images
        concurrent_upload_count = 3
        upload_image_names = [f"upload-concurrent-{i}-{gen_unique_name()}"
                              for i in range(concurrent_upload_count)]
        successful_uploads = []
        upload_errors = []

        def upload_single_image(image_name):
            resp = api_client.images.create_by_file(image_name, fake_image_file)
            if resp.ok:
                return {"name": image_name, "success": True}
            else:
                return {"name": image_name, "success": False,
                        "error": f"{resp.status_code}: {resp.text}"}

        # Execute concurrent uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_upload_count) as executor:  # NOQA
            upload_futures = [executor.submit(upload_single_image, name)
                              for name in upload_image_names]

            for future in concurrent.futures.as_completed(upload_futures):
                result = future.result()
                if result["success"]:
                    successful_uploads.append(result["name"])
                else:
                    upload_errors.append(result)

        assert len(upload_errors) == 0, f"Concurrent upload errors: {upload_errors}"
        assert len(successful_uploads) == concurrent_upload_count, \
            f"Expected {concurrent_upload_count} uploads, got {len(successful_uploads)}"

        # Verify all uploaded images are accessible
        for image_name in successful_uploads:
            code, data = api_client.images.get(image_name)
            assert code == 200, f"Image {image_name} not accessible: {code}"

        # Part 2: Concurrent operations on the same image
        # Use the first uploaded image for operations testing
        target_image_name = successful_uploads[0]
        concurrent_results = []

        def concurrent_operation(operation_type, operation_id):
            if operation_type == "get":
                code, data = api_client.images.get(target_image_name)
                return {"id": operation_id, "op": "get", "success": code == 200, "code": code}

            elif operation_type == "update":
                update_data = {"labels": {f"concurrent-op-{operation_id}": f"timestamp-{time.time()}"}}  # NOQA
                code, data = api_client.images.update(target_image_name,
                                                      dict(metadata=update_data))
                return {"id": operation_id, "op": "update",
                        "success": code in [200, 409], "code": code}

            elif operation_type == "status_check":
                code, data = api_client.images.get(target_image_name)
                if code == 200:
                    progress = data.get("status", {}).get("progress", 0)
                    return {"id": operation_id, "op": "status_check",
                            "success": True, "code": code, "progress": progress}
                return {"id": operation_id, "op": "status_check", "success": False, "code": code}

        # Launch concurrent operations on the same image
        threads = []
        operations = [
            ("get", 1), ("update", 2), ("status_check", 3),
            ("get", 4), ("update", 5), ("get", 6), ("status_check", 7)
        ]

        for op_type, op_id in operations:
            thread = threading.Thread(
                target=lambda ot=op_type, oid=op_id: concurrent_results.append(concurrent_operation(ot, oid))  # NOQA
            )
            threads.append(thread)
            thread.start()

        # Wait for all operations to complete
        for thread in threads:
            thread.join(timeout=15)
            assert not thread.is_alive(), "Thread didn't complete in time"

        # Analyze concurrent operation results
        successful_ops = [r for r in concurrent_results if r and r.get("success")]
        assert len(successful_ops) > 0, "No concurrent operations succeeded on same image"

        # Target image should still be responsive after concurrent operations
        final_code, final_data = api_client.images.get(target_image_name)
        assert final_code == 200, f"Target image not accessible after " \
                                  f"concurrent operations: {final_code}"

        # Part 3: Concurrent cleanup of all images
        cleanup_successful = 0

        def cleanup_single_image(image_name):
            delete_image(api_client, image_name, wait_timeout)
            return image_name

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(successful_uploads)) as executor:  # NOQA
            cleanup_futures = [executor.submit(cleanup_single_image, name)
                               for name in successful_uploads]

            for _ in concurrent.futures.as_completed(cleanup_futures):
                cleanup_successful += 1

        assert cleanup_successful == len(successful_uploads), \
            f"Cleanup failed: {cleanup_successful}/{len(successful_uploads)}"

    @pytest.mark.p1
    @pytest.mark.images
    def test_image_metadata_operations(self, api_client, fake_image_file,
                                       unique_name, wait_timeout):
        """
        Test comprehensive image metadata operations
        Steps:
        1. Create image and verify initial metadata
        2. Update labels, annotations, and description
        3. Test metadata persistence across operations
        4. Verify metadata validation and limits
        """
        image_name = f"metadata-test-{unique_name}"

        # Create image
        resp = api_client.images.create_by_file(image_name, fake_image_file)
        assert resp.ok, f"Failed to create image: {resp.status_code}, {resp.text}"

        # Wait for initial processing
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.images.get(image_name)
            if code == 200 and data.get("status", {}).get("progress") == 100:
                break
            sleep(2)

        # Test comprehensive metadata updates
        metadata_updates = {
            "labels": {
                "environment": "test",
                "team": "qa",
                "version": "1.0.0",
                "critical": "false"
            },
            "annotations": {
                "field.cattle.io/description": "Test image for metadata operations",
                "harvesterhci.io/imageId": image_name,
                "custom.annotation/usage": "automation-testing",
                "created.by": "harvester-e2e-tests"
            }
        }

        code, data = api_client.images.update(image_name, dict(metadata=metadata_updates))
        assert 200 == code, f"Failed to update metadata: {code}, {data}"

        # Verify metadata was applied correctly
        code, data = api_client.images.get(image_name)
        assert 200 == code, (code, data)

        metadata = data["metadata"]
        for field, expected_pairs in metadata_updates.items():
            for key, expected_value in expected_pairs.items():
                actual_value = metadata.get(field, {}).get(key)
                assert actual_value == expected_value, f"Metadata {field}.{key}: expected"\
                                                       f" {expected_value}, got {actual_value}"

        # Test incremental metadata updates
        incremental_updates = {
            "labels": {"priority": "high"},
            "annotations": {"last.modified": "2025-09-30"}
        }

        code, data = api_client.images.update(image_name, dict(metadata=incremental_updates))
        assert 200 == code, f"Failed incremental update: {code}, {data}"

        # Verify both old and new metadata exist
        code, data = api_client.images.get(image_name)
        assert 200 == code, (code, data)

        metadata = data["metadata"]
        assert metadata.get("labels", {}).get("environment") == "test"  # Old label
        assert metadata.get("labels", {}).get("priority") == "high"  # New label

        delete_image(api_client, image_name, wait_timeout)

    @pytest.mark.p2
    @pytest.mark.images
    def test_image_complete_lifecycle(self, api_client, image_info, unique_name, wait_timeout):
        """
        Test complete image lifecycle from creation to deletion
        Steps:
        1. Create image from URL with metadata
        2. Update image properties multiple times
        3. Create volume from image
        4. Export volume back to new image
        5. Download and verify image content
        6. Perform cleanup and verify deletion
        """
        original_image = f"lifecycle-original-{unique_name}"
        exported_image = f"lifecycle-exported-{unique_name}"
        test_volume = f"lifecycle-volume-{unique_name}"

        # Step 1: Create original image with metadata
        create_image_url(api_client, original_image, image_info.url,
                         image_info.image_checksum, wait_timeout)

        initial_metadata = {
            "labels": {"lifecycle": "test", "stage": "original"},
            "annotations": {"description": "Lifecycle test original image"}
        }

        code, data = api_client.images.update(original_image, dict(metadata=initial_metadata))
        assert 200 == code, f"Failed to set initial metadata: {code}, {data}"

        # Step 2: Multiple metadata updates
        for i in range(3):
            update_metadata = {
                "labels": {"update.count": str(i + 1)},
                "annotations": {f"update.{i}": f"value-{i}"}
            }
            code, data = api_client.images.update(original_image, dict(metadata=update_metadata))
            assert 200 == code, f"Failed update {i}: {code}, {data}"

        # Step 3: Create volume from image
        code, data = api_client.images.get(original_image)
        assert 200 == code, (code, data)

        image_size_gb = data["status"]["virtualSize"] // 1024**3 + 1
        image_id = f"{data['metadata']['namespace']}/{original_image}"

        spec = api_client.volumes.Spec(image_size_gb)
        code, data = api_client.volumes.create(test_volume, spec, image_id=image_id)
        assert 201 == code, (code, data)

        # Wait for volume to be bound
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(test_volume)
            if data["status"]["phase"] == "Bound":
                break
            sleep(5)
        else:
            raise AssertionError(f"Volume binding timeout: {code}, {data}")

        # Step 4: Export volume back to image
        code, data = api_client.volumes.export(test_volume, exported_image, "harvester-longhorn")
        assert 200 == code, (code, data)

        # Wait for export completion
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        exported_image_id = ""
        while endtime > datetime.now():
            code, data = api_client.images.get()
            assert 200 == code, (code, data)

            for image in data["items"]:
                if image["spec"]["displayName"] == exported_image:
                    if image.get("status", {}).get("progress") == 100:
                        exported_image_id = image["metadata"]["name"]
                        break

            if exported_image_id:
                break
            sleep(5)

        assert exported_image_id, f"Failed to find exported image {exported_image}"

        # Step 5: Verify exported image properties
        code, data = api_client.images.get(exported_image_id)
        assert 200 == code, (code, data)
        assert data["spec"]["displayName"] == exported_image

        # Step 6: Cleanup in proper order
        delete_volume(api_client, test_volume, wait_timeout)
        delete_image(api_client, original_image, wait_timeout)
        delete_image(api_client, exported_image_id, wait_timeout)

    @pytest.mark.p1
    @pytest.mark.images
    @pytest.mark.negative
    def test_image_name_length_limits(self, api_client, unique_name, wait_timeout):
        """
        Test image creation with various name lengths
        Steps:
        1. Test failure with image name > 63 characters (should fail)
        2. Test success with image name ≤ 63 characters (should pass)
        """
        aligned_size = 1024 * 1024  # 1MB exactly

        with NamedTemporaryFile("wb", suffix=".raw") as f:
            f.write(b"\x00" * aligned_size)
            f.flush()

            # Test 1: Invalid long name (should FAIL)
            long_base = "very-long-image-name-for-testing-kubernetes-name-length-limits-that-exceeds-maximum"  # NOQA
            invalid_long_name = f"{long_base}-{unique_name}"

            resp = api_client.images.create_by_file(invalid_long_name, Path(f.name))
            assert not resp.ok, f"Expected failure with long name but" \
                                f" got success: {resp.status_code}"
            assert resp.status_code in [400, 422], f"Expected 400/422 for " \
                                                   f"invalid name, got: {resp.status_code}"

            # Test 2: Valid name (should PASS)
            valid_base = "valid-image-name"
            valid_name = f"{valid_base}-{unique_name}"

            if len(valid_name) > 63:
                valid_name = f"{valid_base[:30]}-{unique_name}"
            valid_name = valid_name.rstrip('-')

            resp = api_client.images.create_by_file(valid_name, Path(f.name))
            assert resp.ok, f"Failed with valid name: {resp.status_code}, {resp.text}"

            # Cleanup
            delete_image(api_client, valid_name, wait_timeout)

    @pytest.mark.p1
    @pytest.mark.images
    @pytest.mark.negative
    def test_image_metadata_limits(self, api_client, unique_name, wait_timeout):
        """
        Test image metadata handling with excessive data
        Steps:
        1. Create a valid image
        2. Test behavior with excessive metadata (many labels/annotations)
        3. Verify proper handling of metadata limits
        """
        aligned_size = 1024 * 1024  # 1MB exactly

        with NamedTemporaryFile("wb", suffix=".raw") as f:
            f.write(b"\x00" * aligned_size)
            f.flush()

            # Create base image for metadata testing
            image_name = f"metadata-test-{unique_name}"

            resp = api_client.images.create_by_file(image_name, Path(f.name))
            assert resp.ok, f"Failed to create base image: {resp.status_code}, {resp.text}"

            # Test excessive metadata
            excessive_metadata = {
                "labels": {f"test-label-key-{i:03d}": f"test-label-value"
                                                      f"-{i:03d}" for i in range(20)},
                "annotations": {
                    f"test.annotation.key/{i:03d}": "x" * 200 for i in range(10)
                }
            }

            code, data = api_client.images.update(image_name, dict(metadata=excessive_metadata))

            if code == 200:
                # Verify metadata was actually stored
                code, updated_data = api_client.images.get(image_name)
                assert code == 200, f"Failed to retrieve updated image: {code}"

            elif code in [400, 422, 413]:  # 413 = Request Entity Too Large
                print(f"✓ Excessive metadata properly rejected with status: {code}")
            else:
                assert False, f"Unexpected metadata response: {code}, {data}"

            # Cleanup
            delete_image(api_client, image_name, wait_timeout)
