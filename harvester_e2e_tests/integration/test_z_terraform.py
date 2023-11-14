import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.terraform"
]


@pytest.fixture(scope="module")
def ssh_key_resource(ssh_keypair, unique_name, tf_resource):
    pub_key, _ = ssh_keypair
    spec = tf_resource.ssh_key(f"tf_{unique_name}", unique_name, pub_key)
    return spec, unique_name, pub_key


@pytest.fixture(scope="module")
def volume_resource(unique_name, tf_resource):
    size = "2Gi"
    spec = tf_resource.volume(f"tf_{unique_name}", unique_name, size)
    return spec, unique_name, size


@pytest.fixture(scope="module")
def image_resource(unique_name, image_opensuse, tf_resource):
    spec = tf_resource.image_download(
        f"tf_{unique_name}", unique_name, unique_name, image_opensuse.url
    )
    return spec, unique_name, image_opensuse


@pytest.mark.dependency(name="create_ssh_key")
def test_create_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource
    tf_harvester.save_as(spec.ctx, "ssh_key")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.keypairs.get(unique_name)
    assert 200 == code


@pytest.mark.dependency(depends=["create_ssh_key"])
def test_delete_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.keypairs.get(unique_name)
    assert 404 == code


@pytest.mark.dependency(name="create_volume")
def test_create_volume(api_client, tf_harvester, volume_resource):
    spec, unique_name, size = volume_resource
    tf_harvester.save_as(spec.ctx, "volumes")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.volumes.get(unique_name)
    vol_spec = api_client.volumes.Spec.from_dict(data)
    assert 200 == code
    assert size == vol_spec.size


@pytest.mark.dependency(depends=["create_volume"])
def test_delete_volume(api_client, tf_harvester, volume_resource):
    spec, unique_name, _ = volume_resource

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.volumes.get(unique_name)
    assert 404 == code


@pytest.mark.dependency(name="create_image")
def test_create_image(api_client, tf_harvester, image_resource):
    spec, unique_name, img_info = image_resource
    tf_harvester.save_as(spec.ctx, "images")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.images.get(unique_name)
    assert 200 == code
    assert img_info.url == data['spec']['url']


def test_create_volume_from_image(api_client, tf_harvester, tf_resource, image_resource):
    spec, unique_name, img_info = image_resource
    tf_harvester.save_as(spec.ctx, "images")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.images.get(unique_name)
    spec = tf_resource.volume(
        f"tf_{unique_name}", unique_name, "10Gi",
        image=f"{data['metadata']['namespace']}/{unique_name}"
    )
    tf_harvester.save_as(spec.ctx, "vol_from_img")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code


@pytest.mark.dependency(depends=["create_image"])
def test_delete_image(api_client, tf_harvester, image_resource):
    spec, unique_name, _ = image_resource

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.images.get(unique_name)
    assert 404 == code
