
import os

from time import sleep
from datetime import datetime, timedelta
import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.vm',
]


@pytest.mark.images
@pytest.mark.p0
@pytest.mark.dependency(name="create_image_url")
def test_create_with_url(api_client, image_opensuse, unique_name, wait_timeout, sleep_timeout):
    """
    Test if you can create an image from a URL.

    def teardown_class(self):
        os.system('rm *.gzps')
        os.system('rm *.qcow2')

    @pytest.mark.images_p1
    @pytest.mark.dependency(name="create_image_from_volume")
    def test_create_image_from_volume(self, api_client, unique_name, export_storage_class):
        """
    Test create image from volume

    Steps:
        1. Create a volume "test-volume" in Volumes page
        2. Export the volume to image "export-image"
        3. Check the image "export-image" exists
        4. Cleanup image "export-image" on Images page
        5. Cleanup volume "test-volume" on Volumes page
        """

        spec = api_client.volumes.Spec(1)
        code, data = api_client.volumes.create(unique_name, spec)

        assert 201 == code, (code, data)

        api_client.volumes.get(unique_name)
        sleep(5)
        api_client.volumes.export(unique_name, unique_name, export_storage_class)
        sleep(30)

        image_id = self.get_export(api_client, unique_name)

        self.delete_image(api_client, image_id, 10)

        self.delete_volume(api_client, unique_name, 10)

    @pytest.mark.images_p1
    @pytest.mark.dependency(name="create_image_url")
    def test_create_image_url(self, api_client, qcow2_image_url, iso_image_url):
        """
        Test create raw and iso type image from url

        Steps:
        1. Open image page and select default URL
        2. Input qcow2 image file download URL, wait for download complete
        3. Check the qcow2 image exists
        4. Input iso image file download URL, wait for download complete
        5. Check the iso image exists
        """

        self.create_image_url(api_client, 'opensuse', qcow2_image_url, 600)
        self.create_image_url(api_client, 'k3os', iso_image_url, 600)

    @pytest.mark.images_p1
    @pytest.mark.dependency(name="create_image_file")
    def test_upload_image_file(self, api_client):
        """
        Test create raw and iso type image from file

        Steps:
        1. Open image page and select default URL
        2. Upload an qcow2 file type image from file
        3. Check the the uploaded file exists
        """

        self.upload_file(api_client, 'test-file-upload', 'test-upload.qcow2', '10M')

        self.get_image(api_client, 'test-file-upload')

    @pytest.mark.images_p1
    @pytest.mark.dependency(depends=["create_image_url", "create_image_file"])
    def test_delete_image_recreate(self, api_client, iso_image_url):
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

        self.get_image(api_client, 'k3os')
        self.delete_image(api_client, 'k3os', 15)

        self.create_image_url(api_client, 'k3os', iso_image_url, 600)

        self.get_image(api_client, 'test-file-upload')
        self.delete_image(api_client, 'test-file-upload', 15)

        self.upload_file(api_client, 'test-file-upload', 'test-upload.qcow2', '10M')

    @pytest.mark.images_p1
    def test_create_invalid_url(self, api_client, unique_name):
        """
        Test create image from invalid url

        Steps:
        1. Create image with invalid URL. e.g. - https: // test.img
        2. Check the Image state show as Failed
        """
        self.create_with_invalid_url(api_client, unique_name)

    @pytest.mark.images_p1
    def test_create_invalid_file(self, api_client):
        """
        Test create upload image from invalid file type

        Steps:
        1. Try to upload invalid image file to images page, something like dmg, or tar.gzps
        2. Check should get an error
        """

        os.system('''cat <<-EOF >>test-invalid.tar.gzps \ntest\nEOF''')
        resp = api_client.images.create_by_file('test-invalid-file', 'test-invalid.tar.gzps')

        assert 500 == resp.status_code, (
            f"Failed to upload unsupported file type:{resp.status_code}, {resp.content}"
        )

    @pytest.mark.images_p1
    @pytest.mark.dependency(name="edit_image_in_use")
    def test_edit_image_in_use(self, api_client, unique_name):
        """
        Test can edit image which already in use

        Steps:
        1. Check the image created from URL exists
        2. Create a VM and use the existing image created from url
        3. Update the image labels and description
        4. Check can change the image content
        """

        self.get_image(api_client, 'k3os')

        spec = api_client.vms.Spec(1, 1)
        spec.add_image('k3os', "default/k3os")
        code, data = api_client.vms.create(unique_name, spec)

        assert 201 == code, (f"Failed to create vm with error: {code}, {data}")

        updates = {
            "labels": {
                "usage-label": "yes"
            },
            "annotations": {
                "field.cattle.io/description": 'edit image in use'
            },

        }

        self.update_by_input(api_client, 'k3os', updates)

    @pytest.mark.images_p1
    @pytest.mark.dependency(name="edit_image_not_in_use")
    def test_edit_image_not_in_use(self, api_client, qcow2_image_url, iso_image_url):
        """
        Test can edit image which not in use

        Steps:
        1. Check the image created from URL exists
        2. Update the image labels and description
        3. Check can change the image content
        """

        self.get_image(api_client, 'k3os')

        updates = {
            "labels": {
                "usage-label": "no"
            },
            "annotations": {
                "field.cattle.io/description": 'edit image not in use'
            },

        }

        self.update_by_input(api_client, 'opensuse', updates)

    def update_by_input(self, api_client, unique_name, updates):

        code, data = api_client.images.update(unique_name, dict(metadata=updates))

        assert 200 == code, (f"Failed to update image with error: {code}, {data}")

        unexpected = list()
        for field, pairs in updates.items():
            for k, val in pairs.items():
                if data['metadata'][field].get(k) != val:
                    unexpected.append((field, k, val, data['metadata'][field].get(k)))

        assert not unexpected, (
            "\n".join(f"Update {f} failed, set key {k} as {v} but got {n}"
                      for f, k, v, n in unexpected)
        )

    def upload_file(self, api_client, unique_name, file_name, size):
        create_image_cmd = "qemu-img create " + file_name + " " + size
        os.system(create_image_cmd)
        resp = api_client.images.create_by_file(unique_name, file_name)

        assert 200 == resp.status_code, (
            f"Failed to upload fake image with error:{resp.status_code}, {resp.content}"
        )

    def get_export(self, api_client, display_name):
        code, data = api_client.images.get()
        assert 200 == code, (code, data)

        for item in data['items']:
            if item['spec']['displayName'] == display_name:
                image_name = item['metadata']['name']
                break
            else:
                raise AssertionError(
                    f"Failed to find image {display_name}"
                )
        return image_name

    def create_image_url(self, api_client, display_name, image_url, wait_timeout):
        code, data = api_client.images.create_by_url(display_name, image_url)

        assert 201 == code, (code, data)
        image_spec = data.get('spec')

        assert display_name == image_spec.get('displayName')
        assert "download" == image_spec.get('sourceType')

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.images.get(display_name)
            image_status = data.get('status', {})

            assert 200 == code, (code, data)
            if image_status.get('progress') == 100:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to download image {display_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    def delete_image(self, api_client, unique_name, wait_timeout):
        code, data = api_client.images.delete(unique_name)

        assert 200 == code, (f"Failed to delete image with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete image {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    def delete_volume(self, api_client, unique_name, wait_timeout):
        code, data = api_client.volumes.delete(unique_name)

        assert 200 == code, (f"Failed to delete volume with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete volume {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    def get_image(self, api_client, unique_name):
        code, data = api_client.images.get()

        assert len(data['items']) > 0, (code, data)

    1. Create an image from URL.
    2. Check for 201 response.
    3. loop until the image has conditions.
    4. Check if the image is intialzied and the status is true
    5. Remove image
    """
    code, data = api_client.images.create_by_url(unique_name, image_opensuse.url)
    assert 201 == code, (
        f"Failed to create image {unique_name} from URL got\n"
        f"Creation got {code} with {data}"
    )
    endtime = datetime.now() + timedelta(wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name']

    def create_with_invalid_url(self, api_client, unique_name):
        code, data = api_client.images.create_by_url(unique_name, f"https://{unique_name}.img")

        assert 201 == code, (code, data)

        endtime = datetime.now() + timedelta(minutes=3)
        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            image_conds = data.get('status', {}).get('conditions', [])
            if len(image_conds) > 0:
                break
            sleep(3)

        assert len(image_conds) == 1, f"Got unexpected image conditions!\n{data}"
        assert "Initialized" == image_conds[0].get("type")
        assert "False" == image_conds[0].get("status")
        assert "no such host" in image_conds[0].get("message")

        api_client.images.delete(unique_name)
