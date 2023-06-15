from tempfile import NamedTemporaryFile
from pathlib import Path
from time import sleep
from datetime import datetime, timedelta

import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_endpoints",
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.volume",
    "harvester_e2e_tests.fixtures.session",
    "harvester_e2e_tests.fixtures.image",
    "harvester_e2e_tests.fixtures.images",
]


@pytest.fixture(params=["image_opensuse", "image_k3s"])
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


def create_image_url(api_client, name, image_url, wait_timeout):
    code, data = api_client.images.create_by_url(name, image_url)

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


@pytest.mark.p0
class TestBackendImages:
    @pytest.mark.p0
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

    @pytest.mark.p0
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
        create_image_url(api_client, image_name, image_url, wait_timeout)

    @pytest.mark.p0
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

        get_image(api_client, image_name)
        delete_image(api_client, image_name, wait_timeout)

        create_image_url(api_client, image_name, image_url, wait_timeout)
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

    @pytest.mark.p0
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

    @pytest.mark.p0
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

        image_id = data["metadata"]["uid"]

        # Create volume from image_id
        spec = api_client.volumes.Spec(1)
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
