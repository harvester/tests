import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
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


@pytest.mark.dependency(name="create_ssh_key")
def test_create_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource
    tf_harvester.save_as(spec.ctx, "ssh_key")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert 0 == code and not err

    code, data = api_client.keypairs.get(unique_name)
    assert 200 == code


@pytest.mark.dependency(depends=["create_ssh_key"])
def test_delete_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert 0 == code and not err

    code, data = api_client.keypairs.get(unique_name)
    assert 404 == code


@pytest.mark.dependency(name="create_volume")
def test_create_volume(api_client, tf_harvester, volume_resource):
    spec, unique_name, size = volume_resource
    tf_harvester.save_as(spec.ctx, "volumes")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert 0 == code and not err

    code, data = api_client.volumes.get(unique_name)
    vol_spec = api_client.volumes.Spec.from_dict(data)
    assert 200 == code
    assert size == vol_spec.size


@pytest.mark.dependency(depends=["create_volume"])
def test_delete_volume(api_client, tf_harvester, volume_resource):
    spec, unique_name, _ = volume_resource
    tf_harvester.save_as(spec.ctx, "volumes")

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert 0 == code and not err

    code, data = api_client.volumes.get(unique_name)
    assert 404 == code
