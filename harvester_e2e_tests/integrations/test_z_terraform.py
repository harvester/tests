import json
from datetime import datetime, timedelta

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


@pytest.fixture(scope="module")
def clusternetwork_resource(unique_name, tf_resource):
    name = f"cnet-{datetime.strptime(unique_name, '%Hh%Mm%Ss%f-%m-%d').strftime('%H%M%S')}"
    spec = tf_resource.cluster_network(f"tf_{unique_name}", name)
    return spec, name


@pytest.fixture(scope="module")
def vlanconfig_resource(request, unique_name, tf_resource, clusternetwork_resource):
    vlan_nic = request.config.getoption('--vlan-nic')
    assert vlan_nic, f"VLAN NIC {vlan_nic} not configured correctly."

    _, clusternetwork_name = clusternetwork_resource
    name, nics = f"{clusternetwork_name}-{vlan_nic}".lower(), [vlan_nic]
    spec = tf_resource.vlanconfig(f"tf_{unique_name}", name, clusternetwork_name, nics)

    return spec, name, clusternetwork_name, nics


@pytest.fixture(scope="module")
def vmnetwork_resource(request, unique_name, tf_resource, clusternetwork_resource):
    vlan_id = request.config.getoption('--vlan-id')
    assert 4095 > vlan_id > 0, (f"VLAN ID should in range 1-4094, not {vlan_id}")

    _, clusternetwork_name = clusternetwork_resource
    spec = tf_resource.network(f"tf_{unique_name}", unique_name, vlan_id, clusternetwork_name)

    return spec, unique_name, vlan_id, clusternetwork_name


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(name="create_ssh_key")
def test_create_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource
    tf_harvester.save_as(spec.ctx, "ssh_key")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.keypairs.get(unique_name)
    assert 200 == code


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(depends=["create_ssh_key"])
def test_delete_ssh_key(api_client, tf_harvester, ssh_key_resource):
    spec, unique_name, _ = ssh_key_resource

    out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.keypairs.get(unique_name)
    assert 404 == code


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(name="create_volume")
def test_create_volume(api_client, tf_harvester, volume_resource):
    spec, unique_name, size = volume_resource
    tf_harvester.save_as(spec.ctx, "volumes")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.volumes.get(unique_name)
    assert 200 == code
    vol_spec = api_client.volumes.Spec.from_dict(data)
    assert size == vol_spec.size


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(depends=["create_volume"])
def test_delete_volume(api_client, wait_timeout, tf_harvester, volume_resource):
    spec, unique_name, _ = volume_resource

    out, err, rc = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == rc

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.volumes.get(unique_name)
        if 404 == code:
            break
    else:
        raise AssertionError(
            "Terraform destroy volume fail\n"
            f"stdout: {out}\nstderr:{err}, code: {rc}"
        )


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(name="create_image")
def test_create_image(api_client, tf_harvester, image_resource):
    spec, unique_name, img_info = image_resource
    tf_harvester.save_as(spec.ctx, "images")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.images.get(unique_name)
    assert 200 == code
    assert img_info.url == data['spec']['url']


@pytest.mark.p0
@pytest.mark.terraform
def test_create_volume_from_image(api_client, tf_harvester, tf_resource, image_resource):
    spec, unique_name, img_info = image_resource
    tf_harvester.save_as(spec.ctx, "images")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.images.get(unique_name)

    vol_name, size = f"vol-from-img-{unique_name}", "10Gi"
    spec = tf_resource.volume(
        f"tf_{vol_name}", vol_name, size, image=f"{data['metadata']['namespace']}/{unique_name}"
    )
    tf_harvester.save_as(spec.ctx, "vol_from_img")

    out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = api_client.volumes.get(vol_name)
    assert 200 == code
    vol_spec = api_client.volumes.Spec.from_dict(data)
    assert size == vol_spec.size

    # Teardown
    api_client.volumes.delete(vol_name)


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.dependency(depends=["create_image"])
def test_delete_image(api_client, wait_timeout, tf_harvester, image_resource):
    spec, unique_name, _ = image_resource

    out, err, rc = tf_harvester.destroy_resource(spec.type, spec.name)
    assert not err and 0 == rc

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        if 404 == code:
            break
    else:
        raise AssertionError(
            "Terraform destroy image fail\n"
            f"stdout: {out}\nstderr: {err}, code: {rc}"
        )


@pytest.mark.p0
@pytest.mark.terraform
class TestNetworking:
    @pytest.mark.dependency(name="create_clusternetwork")
    def test_create_clusternetwork(self, api_client, tf_harvester, clusternetwork_resource):
        spec, unique_name = clusternetwork_resource
        tf_harvester.save_as(spec.ctx, "clusternetwork")

        out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
        assert not err and 0 == code

        code, data = api_client.clusternetworks.get(unique_name)
        assert 200 == code

    @pytest.mark.dependency(name="create_vlanconfig", depends=["create_clusternetwork"])
    def test_create_vlanconfig(self, api_client, tf_harvester, vlanconfig_resource):
        spec, unique_name, cnet_name, nics = vlanconfig_resource
        tf_harvester.save_as(spec.ctx, "vlanconfig")

        out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
        assert not err and 0 == code

        code, data = api_client.clusternetworks.get_config(unique_name)
        assert 200 == code
        assert cnet_name == data['spec']['clusterNetwork']
        assert nics == data['spec']['uplink']['nics']

    @pytest.mark.dependency(name="create_vm_network", depends=["create_vlanconfig"])
    def test_create_vm_network(self, api_client, tf_harvester, vmnetwork_resource):
        spec, unique_name, vlan_id, cnet_name = vmnetwork_resource
        tf_harvester.save_as(spec.ctx, "vmnetwork")

        out, err, code = tf_harvester.apply_resource(spec.type, spec.name)
        assert not err and 0 == code

        code, data = api_client.networks.get(unique_name)
        assert 200 == code
        config = json.loads(data['spec'].get('config', ""))
        assert vlan_id == config['vlan']
        assert cnet_name in config['bridge']

    @pytest.mark.dependency(depends=["create_vm_network"])
    def test_delete_vm_network(self, api_client, tf_harvester, vmnetwork_resource):
        spec, unique_name, *_ = vmnetwork_resource

        out, err, code = tf_harvester.destroy_resource(spec.type, spec.name)
        assert not err and 0 == code

        code, data = api_client.networks.get(unique_name)
        assert 404 == code

    @pytest.mark.dependency(depends=["create_vlanconfig"])
    def test_delete_vlanconfig(self, api_client, wait_timeout, tf_harvester, vlanconfig_resource):
        spec, unique_name, *_ = vlanconfig_resource

        out, err, rc = tf_harvester.destroy_resource(spec.type, spec.name)
        assert not err and 0 == rc

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.clusternetworks.get_config(unique_name)
            if 404 == code:
                break
        else:
            raise AssertionError(
                "Terraform destroy vlanconfig fail\n"
                f"stdout: {out}\nstderr: {err}, code: {rc}"
            )

    @pytest.mark.dependency(depends=["create_clusternetwork"])
    def test_delete_clusternetwork(
        self, api_client, wait_timeout, tf_harvester, clusternetwork_resource
    ):
        spec, unique_name, *_ = clusternetwork_resource

        out, err, rc = tf_harvester.destroy_resource(spec.type, spec.name)
        assert not err and 0 == rc

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.clusternetworks.get(unique_name)
            if 404 == code:
                break
        else:
            raise AssertionError(
                "Terraform destroy clusternetwork fail\n"
                f"stdout: {out}\nstderr: {err}, code: {rc}"
            )
