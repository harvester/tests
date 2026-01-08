import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
]

# Encryption-related constants
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


@pytest.fixture(scope="module")
def shared_image(api_client, image_ubuntu, unique_name, image_checker):
    source_image_name = f"shared-ubuntu-{unique_name}"
    image_info = image_ubuntu
    code, _ = api_client.images.create_by_url(
        source_image_name, image_info.url, image_info.image_checksum
    )
    assert code == 201, f"Failed to create image: {code}"

    image_checker.wait_downloaded(source_image_name)

    yield source_image_name

    # Cleanup: delete the image after tests
    code, _ = api_client.images.delete(source_image_name)
    if code == 200:
        image_checker.wait_deleted(source_image_name)


@pytest.fixture(scope="class", params=SECRET_COMBINATIONS)
def encryption_secret_data(request):
    return request.param


@pytest.fixture(scope="class")
def encrypted_backing_resources(
    api_client, encryption_secret_data, unique_name, image_checker
):
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
        "parameters": {
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
    }
    code, sc = api_client.scs.create(sc_name, **sc_parameters)
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
            image_checker.wait_deleted(image_name)

    code, data = api_client.scs.delete(sc_name)
    assert code == 200, f"Failed to delete storage class: {code}, {data}"

    code, data = api_client.secrets.delete(secret_name, namespace=namespace)
    assert code == 200, (f"Failed to delete secret: {code}, {data}")


@pytest.fixture(params=INVALID_SECRET_COMBINATIONS)
def invalid_encryption_secret_data(request):
    return request.param


@pytest.fixture
def created_invalid_secret(
    api_client, invalid_encryption_secret_data, unique_name
):
    """
    Create an invalid encryption secret, yield the name, and cleanup after test.
    """
    namespace = "default"
    invalid_secret_name = f"invalid-encrypted-sc-{unique_name}"
    code, data = api_client.secrets.create(
        name=invalid_secret_name,
        data=invalid_encryption_secret_data,
        namespace=namespace,
    )
    assert code == 201, f"Failed to create invalid secret: {code}, {data}"

    yield invalid_secret_name

    # Teardown: delete secret if it was created
    code, data = api_client.secrets.delete(invalid_secret_name, namespace=namespace)
    assert code == 200, f"Failed to delete invalid secret: {code}, {data}"


@pytest.mark.p0
@pytest.mark.skip_if_version("< v1.4.0", reason="New feature after v1.4.0")
class TestEncryptedBackingImage:
    """
    Integration tests for encrypted and decrypted backing images.
    At least one passed and one failed case are included.
    """

    @pytest.mark.p0
    def test_create_encrypted_image_success(
        self,
        encrypted_backing_resources,
        api_client,
        wait_timeout,
        shared_image,
        image_checker,
    ):
        """
        Test creating an encrypted image (should succeed).
        """
        source_image_name = shared_image
        encrypted_image_name = encrypted_backing_resources["encrypted_image_name"]
        namespace = encrypted_backing_resources["namespace"]
        storage_class_name = encrypted_backing_resources["sc_name"]

        code, image = api_client.images.create_by_encrypt(
            source_image_name=source_image_name,
            new_image_name=encrypted_image_name,
            storage_class_name=storage_class_name,
            namespace=namespace,
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
        image_checker.wait_downloaded(encrypted_image_name)

    @pytest.mark.p0
    def test_create_encrypted_image_fail(
        self,
        api_client,
        shared_image,
        encrypted_backing_resources,
    ):
        """
        Test creating an encrypted image with invalid storage class (should fail).
        """
        source_image_name = shared_image
        encrypted_image_name = "fail-encrypted-image"
        namespace = "default"
        storage_class_name = "non-existent-sc"

        code, image = api_client.images.create_by_encrypt(
            source_image_name=source_image_name,
            new_image_name=encrypted_image_name,
            storage_class_name=storage_class_name,
            namespace=namespace,
        )
        assert code != 201, f"Expected failure, but got code {code} with data: {image}"

    @pytest.mark.p0
    def test_create_decrypted_image_success(
            self,
            encrypted_backing_resources,
            api_client,
            wait_timeout,
            image_checker
    ):

        """
        Test creating a decrypted image (should succeed).
        """
        encrypted_image_name = encrypted_backing_resources["encrypted_image_name"]
        decrypted_image_name = encrypted_backing_resources["decrypted_image_name"]
        namespace = encrypted_backing_resources["namespace"]

        code, image = api_client.images.create_by_decrypt(
            source_image_name=encrypted_image_name,
            new_image_name=decrypted_image_name,
            storage_class_name="",  # Decrypted images do not need a encryption storage class
            namespace=namespace,
        )
        assert code == 201, f"Failed to create decrypted image: {code}, {image}"

        code, image = api_client.images.get(decrypted_image_name)
        assert code == 200, f"Decrypted image not found: {code}, {image}"
        assert image["metadata"]["name"] == decrypted_image_name
        assert image["spec"]["securityParameters"]["cryptoOperation"] == "decrypt"
        assert image["spec"]["securityParameters"]["sourceImageName"] == encrypted_image_name
        assert image["spec"]["securityParameters"]["sourceImageNamespace"] == namespace
        image_checker.wait_downloaded(encrypted_image_name)

    @pytest.mark.p0
    def test_create_decrypted_image_fail(self, api_client, encrypted_backing_resources):
        """
        Test creating a decrypted image with non-existent encrypted image (should fail).
        """
        encrypted_image_name = "non-existent-encrypted-image"
        decrypted_image_name = "fail-decrypted-image"
        namespace = "default"

        code, image = api_client.images.create_by_decrypt(
            source_image_name=encrypted_image_name,
            new_image_name=decrypted_image_name,
            storage_class_name="",
            namespace=namespace,
        )

        assert code != 201, f"Expected failure, but got code {code} with data: {image}"


@pytest.mark.p0
@pytest.mark.skip_if_version("< v1.4.0", reason="New feature after v1.4.0")
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
            "parameters": {
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
        }
        code, data = api_client.scs.create(storage_class_name, **sc_parameters)
        assert code == 422, (
            f"Storage class creation should fail for invalid secret: {code}, {data}"
        )
        assert (
            isinstance(data, dict)
            and "message" in data
            and "invalid field" in data["message"]
        ), f"Error message should mention 'invalid field': {data}"
