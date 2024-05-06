from datetime import datetime, timedelta

import pytest


pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    'harvester_e2e_tests.fixtures.rancher_api_client',
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.terraform"
]


# Fixtures
@pytest.fixture(scope="module")
def ubuntu_image(api_client, unique_name, image_ubuntu, wait_timeout):
    rc, data = api_client.images.create_by_url(unique_name, image_ubuntu.url)
    assert 201 == rc, (
        f"Failed to upload ubuntu image with error\n"
        f"rc: {rc}, data:\n{data}"
    )

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = api_client.images.get(unique_name)
        if 200 == rc and image_ubuntu.url == data['spec']['url']:
            break
    else:
        raise AssertionError(
            f"Fail to create image {unique_name}\n"
            f"rc: {rc}, data:\n{data}"
        )
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield {
        "id": f"{namespace}/{name}",
        "ssh_user": "ubuntu"
    }

    api_client.images.delete(name, namespace)


@pytest.fixture(scope='module')
def vlan_network(request, api_client):
    vlan_nic = request.config.getoption('--vlan-nic')
    vlan_id = request.config.getoption('--vlan-id')
    assert -1 != vlan_id, "Rancher integration test needs VLAN"

    api_client.clusternetworks.create(vlan_nic)
    api_client.clusternetworks.create_config(vlan_nic, vlan_nic, vlan_nic)

    network_name = f'vlan-network-{vlan_id}'
    code, data = api_client.networks.get(network_name)
    if code != 200:
        code, data = api_client.networks.create(network_name, vlan_id, cluster_network=vlan_nic)
        assert 201 == code, (
            f"Failed to create network-attachment-definition {network_name}\n"
            f"rc: {code}, data:\n{data}"
        )
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield {
        "id": f"{namespace}/{name}"
    }

    api_client.networks.delete(network_name, namespace)


@pytest.fixture(scope='module')
def harvester(api_client, rancher_api_client, unique_name, wait_timeout):
    """ Rancher creates Harvester entry (Import Existing)
    """
    name = f"hvst-{unique_name}"

    rc, data = rancher_api_client.mgmt_clusters.create_harvester(name)
    assert 201 == rc, (rc, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = rancher_api_client.mgmt_clusters.get(name)
        if data.get('status', {}).get('clusterName'):
            break
    else:
        raise AssertionError(
            f"Fail to get MgmtCluster with clusterName {name}\n"
            f"rc: {rc}, data:\n{data}"
        )
    namespace = data['metadata']['namespace']

    yield {
        "name": name,
        "namespace": namespace,
        "id": data['status']['clusterName'],
        "kubeconfig": api_client.generate_kubeconfig()
    }

    rancher_api_client.mgmt_clusters.delete(name, namespace)
    updates = dict(value="")
    api_client.settings.update("cluster-registration-url", updates)


@pytest.fixture(scope="module")
def rancher(rancher_api_client):
    access_key, secret_key = rancher_api_client.token.split(":")
    yield {
        "endpoint": rancher_api_client.endpoint,
        "token": rancher_api_client.token,
        "access_key": access_key,
        "secret_key": secret_key
    }


@pytest.fixture(scope='module')
def rke2_cluster(unique_name, rke2_version):
    return {
        "name": f"rke2-{unique_name}",
        "id": "",                         # set in test_create_rke2_cluster
        "k8s_version": rke2_version
    }


@pytest.fixture(scope="module")
def credential_resource(unique_name, tf_rancher_resource, harvester):
    return tf_rancher_resource.cloud_credential(
        f"cc-{unique_name}", harvester["name"]
    )


@pytest.fixture(scope="module")
def machine_resource(tf_rancher_resource, rke2_cluster, vlan_network, ubuntu_image):
    return tf_rancher_resource.machine_config(
        rke2_cluster["name"], vlan_network["id"], ubuntu_image["id"], ubuntu_image["ssh_user"]
    )


@pytest.fixture(scope="module")
def cluster_resource(tf_rancher_resource, rke2_cluster, harvester, credential_resource):
    return tf_rancher_resource.cluster_config(
        rke2_cluster["name"], rke2_cluster["k8s_version"], harvester["name"],
        credential_resource.name
    )


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="import_harvester")
def test_import_harvester(api_client, rancher_api_client, harvester, wait_timeout):
    # Get cluster registration URL in Rancher's Virtualization Management
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = rancher_api_client.cluster_registration_tokens.get(harvester['id'])
        if 200 == rc and data.get('manifestUrl'):
            break
    else:
        raise AssertionError(
            f"Fail to registration URL for the imported harvester {harvester['name']}\n"
            f"rc: {rc}, data:\n{data}"
        )

    # Set cluster-registration-url on Harvester
    updates = dict(value=data['manifestUrl'])
    rc, data = api_client.settings.update("cluster-registration-url", updates)
    assert 200 == rc, (
        f"Failed to update Harvester's settings `cluster-registration-url`"
        f"rc: {rc}, data:\n{data}"
    )

    # Check Cluster becomes `active` in Rancher's Virtualization Management
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = rancher_api_client.mgmt_clusters.get(harvester['name'])
        cluster_state = data['metadata']['state']
        if "active" == cluster_state['name'] and "Ready" in cluster_state['message']:
            break
    else:
        raise AssertionError(
            f"Fail to import harvester\n"
            f"rc: {rc}, data:\n{data}"
        )


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="create_cloud_credential", depends=["import_harvester"])
def test_create_cloud_credential(rancher_api_client, tf_rancher, credential_resource):
    spec = credential_resource
    tf_rancher.save_as(spec.ctx, "cloud_credential")
    out, err, code = tf_rancher.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    code, data = rancher_api_client.cloud_credentials.get(params={"name": spec.name})
    assert 200 == code, (
        f"Failed to get cloud credential {spec.name}: {code}, {data}"
    )


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="create_machine_config", depends=["create_cloud_credential"])
def test_create_machine_config(tf_rancher, machine_resource):
    spec = machine_resource
    tf_rancher.save_as(spec.ctx, "machine_config")
    out, err, code = tf_rancher.apply_resource(spec.type, spec.name)
    assert not err and 0 == code


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="create_rke2_cluster", depends=["create_machine_config"])
def test_create_rke2_cluster(tf_rancher, rke2_cluster, rancher_api_client, cluster_resource):
    spec = cluster_resource
    tf_rancher.save_as(spec.ctx, "rke2_cluster")
    out, err, code = tf_rancher.apply_resource(spec.type, spec.name)
    assert not err and 0 == code

    rc, data = rancher_api_client.mgmt_clusters.get(rke2_cluster['name'])
    cluster_state = data.get("metadata", {}).get("state", {})
    assert "active" == cluster_state['name'] and \
           "Ready" in cluster_state['message']

    # check deployments
    rke2_cluster['id'] = data["status"]["clusterName"]
    for deployment in ["harvester-cloud-provider", "harvester-csi-driver-controllers"]:
        rc, data = rancher_api_client.cluster_deployments.get(
            rke2_cluster['id'], "kube-system", deployment
        )
        cluster_state = data.get("metadata", {}).get("state", {})
        assert 200 == rc and \
               "active" == cluster_state["name"]


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="delete_rke2_cluster", depends=["create_rke2_cluster"])
def test_delete_rke2_cluster(tf_rancher, rke2_cluster, rancher_api_client, cluster_resource):
    spec = cluster_resource
    out, err, code = tf_rancher.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code

    rc, data = rancher_api_client.mgmt_clusters.get(rke2_cluster['name'])
    assert 404 == rc


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="delete_machine_config", depends=["create_machine_config"])
def test_delete_machine_config(tf_rancher, machine_resource):
    spec = machine_resource
    out, err, code = tf_rancher.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code


@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="delete_cloud_credential", depends=["create_cloud_credential"])
def test_delete_cloud_credential(tf_rancher, credential_resource):
    spec = credential_resource
    out, err, code = tf_rancher.destroy_resource(spec.type, spec.name)
    assert not err and 0 == code
