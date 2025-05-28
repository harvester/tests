import filecmp
import json
import re
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

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


def wait_resource_deleted(get_func, name, wait_timeout, namespace=None, sleep_time=3):
    """
    Long polling until resource is deleted (get_func returns 404) or timeout.
    get_func: function to get the resource, should return (code, data)
    name: resource name
    wait_timeout: timeout in seconds
    namespace: optional, if needed by get_func
    sleep_time: polling interval in seconds
    """
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        if namespace is not None:
            code, _ = get_func(name, namespace=namespace)
        else:
            code, _ = get_func(name)
        if code == 404:
            return
        sleep(sleep_time)
    raise AssertionError(f"Failed to delete resource {name} in {wait_timeout} seconds")


def wait_image_progress(api_client, image_name, wait_timeout):
    """
    Long polling image status until progress == 100 or timeout.
    """
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    last_code, last_data = None, None
    while endtime > datetime.now():
        code, data = api_client.images.get(image_name)
        image_status = data.get("status", {})
        last_code, last_data = code, data

        assert 200 == code, (code, data)
        if image_status.get("progress") == 100:
            return
        sleep(5)
    else:
        raise AssertionError(
            f"Still got {last_code} with {last_data}"
        )


def create_image_url(api_client, name, image_url, image_checksum, wait_timeout):
    code, data = api_client.images.create_by_url(name, image_url, image_checksum)

    assert 201 == code, (code, data)
    image_spec = data.get("spec")

    assert name == image_spec.get("displayName")
    assert "download" == image_spec.get("sourceType")

    wait_image_progress(api_client, name, wait_timeout)


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


# 定義你要測試的 secret 組合
SECRET_COMBINATIONS = [
    {
        "CRYPTO_KEY_CIPHER": "aes-xts-plain64",
        "CRYPTO_KEY_HASH": "sha256",
        "CRYPTO_KEY_PROVIDER": "secret",
        "CRYPTO_KEY_SIZE": "256",
        "CRYPTO_KEY_VALUE": "test",
        "CRYPTO_PBKDF": "argon2i",
    },
    {
        "CRYPTO_KEY_CIPHER": "aes-xts-plain64",
        "CRYPTO_KEY_HASH": "sha512",
        "CRYPTO_KEY_PROVIDER": "secret",
        "CRYPTO_KEY_SIZE": "512",
        "CRYPTO_KEY_VALUE": "test",
        "CRYPTO_PBKDF": "argon2i",
    },
]


@pytest.fixture(scope="class", params=SECRET_COMBINATIONS)
def encryption_secret_data(request):
    return request.param


@pytest.fixture(scope="module")
def shared_image(api_client, image_ubuntu, unique_name, wait_timeout):
    source_image_name = f"shared-ubuntu-{unique_name}"
    image_info = image_ubuntu
    create_image_url(
        api_client,
        source_image_name,
        image_info.url,
        image_info.image_checksum,
        wait_timeout,
    )

    yield source_image_name

    # Cleanup: delete the image after tests
    code, _ = api_client.images.delete(source_image_name)
    if code == 200:
        wait_resource_deleted(api_client.images.get, source_image_name, wait_timeout)


@pytest.fixture(scope="class")
def encrypted_backing_resources(api_client, encryption_secret_data, unique_name, wait_timeout):
    """
    Fixture to create and yield all resources for TestEncryptedBackingImage,
    and clean them up after tests.
    """
    namespace = "default"
    secret_name = f"my-secret-{unique_name}"
    sc_name = f"my-encrypted-sc-{unique_name}"
    encrypted_image_name = f"encrypted-image-{unique_name}"
    decrypted_image_name = f"decrypted-image-{unique_name}"

    # Create secret
    code, data = api_client.secrets.create(
        name=secret_name,
        data=encryption_secret_data,
        namespace=namespace,
    )
    assert code == 201, (code, data)

    # Create storage class
    sc_parameters = {
        "csi.storage.k8s.io/node-publish-secret-name": secret_name,
        "csi.storage.k8s.io/node-publish-secret-namespace": namespace,
        "csi.storage.k8s.io/node-stage-secret-name": secret_name,
        "csi.storage.k8s.io/node-stage-secret-namespace": namespace,
        "csi.storage.k8s.io/provisioner-secret-name": secret_name,
        "csi.storage.k8s.io/provisioner-secret-namespace": namespace,
        "encrypted": "true",
        "migratable": "true",
        "numberOfReplicas": "3",
        "staleReplicaTimeout": "30",
    }
    code, sc = api_client.scs.create_by_parameters(sc_name, sc_parameters)
    assert code == 201, f"Failed to create storage class: {code}, {sc}"

    resources = {
        "namespace": namespace,
        "secret_name": secret_name,
        "sc_name": sc_name,
        "encrypted_image_name": encrypted_image_name,
        "decrypted_image_name": decrypted_image_name,
    }
    yield resources

    # Cleanup: delete images, storage class, secret
    for image_name in [decrypted_image_name, encrypted_image_name]:
        code, data = api_client.images.delete(image_name, namespace=namespace)
        if code == 200:
            wait_resource_deleted(
                api_client.images.get, image_name, wait_timeout, namespace=namespace
            )

    code, data = api_client.scs.delete(sc_name)
    if code == 200:
        wait_resource_deleted(api_client.scs.get, sc_name, wait_timeout)

    code, data = api_client.secrets.delete(secret_name, namespace=namespace)
    if code == 204:
        wait_resource_deleted(
            api_client.secrets.get, secret_name, wait_timeout, namespace=namespace
        )


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
        create_image_url(api_client, image_name, image_url,
                         image_info.image_checksum, wait_timeout)

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


@pytest.mark.p0
@pytest.mark.usefixtures("encrypted_backing_resources")
@pytest.mark.skip_version_if("< v1.4.0", reason="New feature after v1.4.0")
class TestEncryptedBackingImage:
    @pytest.mark.p0
    @pytest.mark.dependency(name="create_encrypted_image")
    def test_create_encrypted_image(
        self,
        encrypted_backing_resources,
        api_client,
        wait_timeout,
        shared_image,
    ):
        source_image_name = shared_image
        encrypted_image_name = encrypted_backing_resources["encrypted_image_name"]
        namespace = encrypted_backing_resources["namespace"]
        storage_class_name = encrypted_backing_resources["sc_name"]

        code, image = api_client.images.create_crypto_image(
            source_image_name=source_image_name,
            new_image_name=encrypted_image_name,
            storage_class_name=storage_class_name,
            namespace=namespace,
            crypto_operation="encrypt"
        )
        assert code == 201, f"Failed to create encrypted image: {code}, {image}"

        code, image = api_client.images.get(encrypted_image_name)
        assert code == 200, f"Encrypted image not found: {code}, {image}"
        assert image["metadata"]["name"] == encrypted_image_name
        assert image["spec"]["securityParameters"]["cryptoOperation"] == "encrypt"
        assert image["spec"]["securityParameters"]["sourceImageName"] == source_image_name
        assert image["spec"]["securityParameters"]["sourceImageNamespace"] == namespace
        assert (
            image["metadata"]["annotations"]["harvesterhci.io/storageClassName"]
            == storage_class_name
        )

        wait_image_progress(api_client, encrypted_image_name, wait_timeout)

    @pytest.mark.p0
    @pytest.mark.dependency(name="create_decrypted_image", depends=["create_encrypted_image"])
    def test_create_decrypted_image(self, encrypted_backing_resources, api_client, wait_timeout):
        encrypted_image_name = encrypted_backing_resources["encrypted_image_name"]
        decrypted_image_name = encrypted_backing_resources["decrypted_image_name"]
        namespace = encrypted_backing_resources["namespace"]

        code, image = api_client.images.create_crypto_image(
            source_image_name=encrypted_image_name,
            new_image_name=decrypted_image_name,
            storage_class_name="",  # Decrypted images do not need a encryption storage class
            crypto_operation="decrypt",
            namespace=namespace,
        )
        assert code == 201, f"Failed to create decrypted image: {code}, {image}"

        code, image = api_client.images.get(decrypted_image_name)
        assert code == 200, f"Decrypted image not found: {code}, {image}"
        assert image["metadata"]["name"] == decrypted_image_name
        assert image["spec"]["securityParameters"]["cryptoOperation"] == "decrypt"
        assert image["spec"]["securityParameters"]["sourceImageName"] == encrypted_image_name
        assert image["spec"]["securityParameters"]["sourceImageNamespace"] == namespace

        wait_image_progress(api_client, decrypted_image_name, wait_timeout)


# Define invalid secret combinations for error testing
INVALID_SECRET_COMBINATIONS = [
    {
        "CRYPTO_KEY_CIPHER": "aes-xts-plain64",
        "CRYPTO_KEY_HASH": "sha256",
        "CRYPTO_KEY_PROVIDER": "secret",
        "CRYPTO_KEY_SIZE": "asdasd",  # invalid
        "CRYPTO_KEY_VALUE": "test",
        "CRYPTO_PBKDF": "argon2i",
    },
    {
        "CRYPTO_KEY_CIPHER": "invalid-cipher",   # invalid
        "CRYPTO_KEY_HASH": "sha256",
        "CRYPTO_KEY_PROVIDER": "secret",
        "CRYPTO_KEY_SIZE": "256",
        "CRYPTO_KEY_VALUE": "test",
        "CRYPTO_PBKDF": "argon2i",
    },
]


@pytest.fixture(params=INVALID_SECRET_COMBINATIONS)
def invalid_encryption_secret_data(request):
    return request.param


@pytest.fixture
def created_invalid_secret(api_client, invalid_encryption_secret_data, unique_name):
    """
    Create an invalid encryption secret, yield the name, and cleanup after test.
    """
    namespace = "default"
    invalid_secret_name = f"invalid-encrypted-sc-{unique_name}"
    code, _ = api_client.secrets.create(
        name=invalid_secret_name,
        data=invalid_encryption_secret_data,
        namespace=namespace,
    )

    yield invalid_secret_name

    # Teardown: delete secret if it was created
    if code == 201 or code == 409:
        api_client.secrets.delete(invalid_secret_name, namespace=namespace)


@pytest.mark.p0
class TestInvalidEncryptionSecret:
    """
    Test creating invalid encryption secrets and verify error handling.
    """

    @pytest.mark.p0
    def test_create_invalid_encryption_secret(self, api_client, created_invalid_secret):
        namespace = "default"
        secret_name = created_invalid_secret
        storage_class_name = secret_name
        sc_parameters = {
            "csi.storage.k8s.io/node-publish-secret-name": secret_name,
            "csi.storage.k8s.io/node-publish-secret-namespace": namespace,
            "csi.storage.k8s.io/node-stage-secret-name": secret_name,
            "csi.storage.k8s.io/node-stage-secret-namespace": namespace,
            "csi.storage.k8s.io/provisioner-secret-name": secret_name,
            "csi.storage.k8s.io/provisioner-secret-namespace": namespace,
            "encrypted": "true",
            "migratable": "true",
            "numberOfReplicas": "3",
            "staleReplicaTimeout": "30",
        }
        code, data = api_client.scs.create_by_parameters(storage_class_name, sc_parameters)
        # Should not be able to create storage class with invalid secret
        assert code == 422, (
            f"Storage class creation should fail for invalid secret: {code}, {data}"
        )
        assert (
            isinstance(data, dict)
            and "message" in data
            and "invalid field" in data["message"]
        ), f"Error message should mention 'invalid field': {data}"
