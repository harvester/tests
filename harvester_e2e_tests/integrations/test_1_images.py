import filecmp
import json
import re
import zlib
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks"
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


@pytest.fixture(scope="class")
def cluster_network(api_client, vlan_nic):
    cnet = f"cnet-{vlan_nic}"
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
def storage_network(api_client, cluster_network, vlan_id, vlan_cidr, wait_timeout, sleep_timeout):
    code, data = api_client.settings.get('storage-network')
    assert 200 == code, (code, data)

    # Enable from Harvester side
    spec_orig = api_client.settings.Spec.from_dict(data)
    spec = api_client.settings.StorageNetworkSpec.enable_with(vlan_id, cluster_network, vlan_cidr)
    code, data = api_client.settings.update('storage-network', spec)
    assert 200 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.settings.get('storage-network')
        conds = data.get('status', {}).get('conditions', [])
        if conds and 'True' == conds[-1].get('status') and 'Completed' == conds[-1].get('reason'):
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"Fail to enable storage-network with error: {code}, {data}"
        )

    # Check on Longhorn side
    done, ip_range = [], ip_network(vlan_cidr)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.get_pods(namespace='longhorn-system')
        lh_instance_mgrs = [d for d in data['data']
                            if 'instance-manager' in d['id'] and d['id'] not in done]
        retries = []
        for im in lh_instance_mgrs:
            if 'Running' != im['status']['phase']:
                retries.append(im)
                continue
            nets = json.loads(im['metadata']['annotations']['k8s.v1.cni.cncf.io/network-status'])
            try:
                dedicated = next(n for n in nets if 'lhnet1' == n.get('interface'))
            except StopIteration:
                retries.append(im)
                continue

            if not all(ip_address(ip) in ip_range for ip in dedicated.get('ips', ['::1'])):
                retries.append(im)
                continue

        if not retries:
            break
        sleep(sleep_timeout)
    else:
        raise AssertionError(
            f"{len(retries)} Longhorn's instance manager not be updated after {wait_timeout}s\n"
            f"Not completed: {retries}"
        )

    yield

    # Teardown
    code, data = api_client.settings.update('storage-network', spec_orig)
    assert 200 == code, (code, data)


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

    @pytest.mark.skip_version_if("> v1.2.0", "<= v1.4.0", reason="Issue#4293 fix after `v1.4.0`")
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


@pytest.mark.p0
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
