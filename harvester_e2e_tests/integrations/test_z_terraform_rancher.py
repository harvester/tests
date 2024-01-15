from datetime import datetime, timedelta

import pytest

# TODO: Drop after debug #
##########################
import pdb
from pprint import pprint


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
        "ssh_user": "ubuntu",
        "id": f"{namespace}/{name}"
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

    yield {
        "id": data['metadata']['name']
    }

    api_client.networks.delete(network_name)


@pytest.fixture(scope='module')
def harvester_cluster(api_client, rancher_api_client, unique_name, wait_timeout):
    """ Rancher creates Harvester entry (Import Existing)
    """
    rc, data = rancher_api_client.mgmt_clusters.create_harvester(unique_name)
    assert 201 == rc, (rc, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = rancher_api_client.mgmt_clusters.get(unique_name)
        if data.get('status', {}).get('clusterName'):
            break
    else:
        raise AssertionError(
            f"Fail to get MgmtCluster with clusterName {unique_name}\n"
            f"rc: {rc}, data:\n{data}"
        )

    yield {
        "name": unique_name,
        "id": data['status']['clusterName']
    }

    rancher_api_client.mgmt_clusters.delete(unique_name)
    updates = dict(value="")
    api_client.settings.update("cluster-registration-url", updates)


# Tests
@pytest.mark.p0
@pytest.mark.terraform
@pytest.mark.rancher
@pytest.mark.dependency(name="import_harvester")
def test_import_harvester(api_client, rancher_api_client, harvester_cluster, wait_timeout):
    # Get cluster registration URL in Rancher's Virtualization Management
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        rc, data = rancher_api_client.cluster_registration_tokens.get(harvester_cluster['id'])
        if 200 == rc and data.get('manifestUrl'):
            break
    else:
        raise AssertionError(
            f"Fail to registration URL for the imported harvester {harvester_cluster['name']}\n"
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
        rc, data = rancher_api_client.mgmt_clusters.get(harvester_cluster['name'])
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
class TestRKE2:
    # @pytest.mark.dependency(depends=["import_harvester"], name="create_rke2")
    def test_create_rke2(self, ubuntu_image, vlan_network):
        
        assert True

