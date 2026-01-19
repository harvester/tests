# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

from json import loads, dumps
from time import sleep
from datetime import datetime, timedelta

import pytest


pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_client',
    'harvester_e2e_tests.fixtures.rancher_api_client',
    "harvester_e2e_tests.fixtures.images",
]


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
            f"Failed to create network-attachment-definition {network_name} \
                with error {code}, {data}"
        )
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield {
        "name": name,
        "id": f"{namespace}/{name}"
    }

    api_client.networks.delete(network_name)


@pytest.fixture(scope="module")
def ip_pool(request, api_client, unique_name, vlan_network):
    name = f"ippool-{unique_name}"
    ip_pool_subnet = request.config.getoption('--ip-pool-subnet')
    ip_pool_start = request.config.getoption('--ip-pool-start')
    ip_pool_end = request.config.getoption('--ip-pool-end')

    code, data = api_client.ippools.create(
        name, ip_pool_subnet, ip_pool_start, ip_pool_end, vlan_network["id"]
    )
    assert 201 == code, (
        f"Failed to create ip pool {name} with error: {code}, {data}"
    )

    yield {
        "name": name,
        "subnet": ip_pool_subnet
    }

    api_client.ippools.delete(name)


@pytest.fixture(scope="module")
def ubuntu_image(api_client, unique_name, image_ubuntu, polling_for):
    name = f"ubuntu-{unique_name}"

    code, data = api_client.images.create_by_url(name, image_ubuntu.url)
    assert 201 == code, (
        f"Failed to upload ubuntu image with error: {code}, {data}"
    )

    code, data = polling_for(
        f"image {name} to be ready",
        lambda code, data: data.get('status', {}).get('progress', None) == 100,
        api_client.images.get, name
    )
    namespace = data['metadata']['namespace']
    name = data['metadata']['name']

    yield {
        "ssh_user": "ubuntu",
        "id": f"{namespace}/{name}"
    }

    api_client.images.delete(name)


@pytest.fixture(scope='module')
def harvester_mgmt_cluster(api_client, rancher_api_client, unique_name, polling_for):
    """ Rancher creates Harvester entry (Import Existing)
    """
    cluster_name = f"hvst-{unique_name}"

    code, data = rancher_api_client.mgmt_clusters.create_harvester(cluster_name)
    assert 201 == code, (
         f"Failed to create Harvester entry {cluster_name} with error: {code}, {data}"
    )

    code, data = polling_for(
        f"finding clusterName in MgmtCluster {cluster_name}",
        lambda code, data: data.get('status', {}).get('clusterName'),
        rancher_api_client.mgmt_clusters.get, cluster_name
    )

    yield {
        "name": cluster_name,
        "id": data['status']['clusterName']     # e.g. c-m-n6bsktxb
    }

    rancher_api_client.mgmt_clusters.delete(cluster_name)
    updates = dict(value="")
    api_client.settings.update("cluster-registration-url", updates)


@pytest.fixture(scope='module')
def harvester_cloud_credential(api_client, rancher_api_client,
                               harvester_mgmt_cluster, unique_name):
    code, data = rancher_api_client.clusters.generate_kubeconfig(
        harvester_mgmt_cluster['id']
    )
    assert 200 == code, (
        f"Failed to create kubconfig with error: {code}, {data}"
    )
    harvester_kubeconfig = data['config']

    code, data = rancher_api_client.cloud_credentials.create(
        unique_name,
        harvester_kubeconfig,
        harvester_mgmt_cluster['id']
    )
    assert 201 == code, (
        f"Failed to create cloud credential with error: {code}, {data}"
    )

    code, data = rancher_api_client.cloud_credentials.get(data['id'])
    assert 200 == code, (
        f"Failed to get cloud credential {data['id']} with error: {code}, {data}"
    )

    yield data

    rancher_api_client.cloud_credentials.delete(data['id'])


@pytest.fixture(scope="module",
                params=[1, 3])
def machine_count(request):
    return request.param


@pytest.fixture(scope='class')
def rke1_cluster(unique_name, rancher_api_client, machine_count, rke1_version):
    name = f"rke1-{unique_name}-{machine_count}"
    yield {
        "name": name,
        "id": "",    # set in Test_RKE1::test_create_rke1, e.g. c-m-n6bsktxb
        "machine_count": machine_count,
        "k8s_version": rke1_version
    }

    rancher_api_client.mgmt_clusters.delete(name)


@pytest.fixture(scope='class')
def rke2_cluster(unique_name, rancher_api_client, machine_count, rke2_version):
    name = f"rke2-{unique_name}-{machine_count}"
    yield {
        "name": name,
        "id": "",    # set in Test_RKE2::test_create_rke2, e.g. c-m-n6bsktxb
        "machine_count": machine_count,
        "k8s_version": rke2_version
    }

    rancher_api_client.mgmt_clusters.delete(name)


@pytest.fixture(scope='class')
def csi_deployment(unique_name):
    yield {
        "namespace": "default",
        "name": f"csi-{unique_name}",
        "image": "nginx:latest",
        "pvc": f"pvc-{unique_name}"
    }


@pytest.fixture(scope='class')
def nginx_deployment(unique_name):
    return {
        "namespace": "default",
        "name": f"nginx-{unique_name}",
        "image": "nginx:latest"
    }


@pytest.fixture(scope="class")
def unset_cpu_memory_overcommit(api_client):
    code, data = api_client.settings.get('overcommit-config')
    assert 200 == code, (code, data)

    origin_val = loads(data.get('value', data['default']))
    spec = api_client.settings.Spec.from_dict(data)
    spec.cpu = spec.memory = 100
    spec.storage = origin_val['storage']
    code, data = api_client.settings.update('overcommit-config', spec)
    assert 200 == code, (code, data)

    yield loads(data['value']), origin_val

    spec.value = origin_val
    api_client.settings.update('overcommit-config', spec)


@pytest.fixture(scope='function', params=["dhcp", "pool"])
def lb_service(request, api_client, unique_name, nginx_deployment, ip_pool):
    namespace = "default"
    name = f"lb-{unique_name}-{request.param}"
    data = {
        "type": "service",
        "metadata": {
            "namespace": namespace,
            "name": name,
            "annotations": {
                "cloudprovider.harvesterhci.io/ipam": request.param
            }
        },
        "spec": {
            "type": "LoadBalancer",
            "sessionAffinity": None,
            "ports": [
                {
                    "name": "http",
                    "port": 8080,
                    "protocol": "TCP",
                    "targetPort": 80
                }
            ],
            "selector": {
                "name": nginx_deployment["name"]
            }
        }
    }

    yield {
        "namespace": namespace,
        "name": name,
        "data": data
    }

    code, data = api_client.loadbalancers.get()
    assert 200 == code, (code, data)
    lbs = data["data"]
    for lb in lbs:
        if name in lb["id"]:
            api_client.loadbalancers.delete(lb["id"])
            break


@pytest.mark.p0
@pytest.mark.rancher
@pytest.mark.dependency(name="import_harvester")
def test_import_harvester(api_client, rancher_api_client, harvester_mgmt_cluster, polling_for):
    # Get cluster registration URL in Rancher's Virtualization Management
    code, data = polling_for(
        f"registration URL for the imported harvester {harvester_mgmt_cluster['name']}",
        lambda code, data: 200 == code and data.get('manifestUrl'),
        rancher_api_client.cluster_registration_tokens.get, harvester_mgmt_cluster['id']
    )

    # Set cluster-registration-url on Harvester
    updates = dict(value=data['manifestUrl'])
    code, data = api_client.settings.update("cluster-registration-url", updates)
    assert 200 == code, (
        f"Failed to update Harvester's settings `cluster-registration-url`"
        f" with error: {code}, {data}"
    )

    # Check Cluster becomes `active` in Rancher's Virtualization Management
    polling_for(
        "harvester to be ready",
        lambda code, data:
            "active" == data['metadata']['state']['name'] and
            "Ready" in data['metadata']['state']['message'],
        rancher_api_client.mgmt_clusters.get, harvester_mgmt_cluster['name']
    )


@pytest.mark.p1
@pytest.mark.rancher
@pytest.mark.dependency(depends=["import_harvester"])
def test_add_project_owner_user(api_client, rancher_api_client, unique_name, wait_timeout,
                                harvester_mgmt_cluster):
    cluster_id = harvester_mgmt_cluster['id']
    username, password = f"user-{unique_name}", unique_name

    spec = rancher_api_client.users.Spec(password)
    # create user
    code, data = rancher_api_client.users.create(username, spec)
    assert 201 == code, (
        f"Failed to create user {username!r}\n"
        f"API Status({code}): {data}"
    )
    uid, upids = data['id'], data['principalIds']

    # add role `user` to user
    code, data = rancher_api_client.users.add_role(uid, 'user')
    assert 201 == code, (
        f"Failed to add role 'user' for user {username!r}\n"
        f"API Status({code}): {data}"
    )

    # Get `Default` project's uid
    cluster_api = rancher_api_client.clusters.explore(cluster_id)
    code, data = cluster_api.projects.get_by_name('Default')
    assert 200 == code, (code, data)
    project_id = data['id']
    # add user to `Default` project as *project-owner*
    code, data = cluster_api.project_members.create(project_id, upids[0], "project-owner")
    assert 201 == code, (code, data)
    proj_muid = data['id']

    # Login as the user
    endpoint = rancher_api_client.endpoint
    user_rapi = rancher_api_client.login(endpoint, username, password, ssl_verify=False)
    user_capi = user_rapi.clusters.explore(cluster_id)
    # Check user can only view the project he joined
    code, data = user_capi.projects.get()
    assert 200 == code, (code, data)
    assert 1 == len(data['data']), (code, data)

    # teardown
    cluster_api.project_members.delete(proj_muid)
    rancher_api_client.users.delete(uid)


@pytest.mark.p0
@pytest.mark.namespace
@pytest.mark.rancher
class TestResourceQuota:
    ns_quota = dict(cpu=3000, mem=4000)

    @pytest.mark.dependency(name="create_project", depends=["import_harvester"])
    def test_create_project(self, rancher_api_client, unique_name, harvester_mgmt_cluster):
        cluster_api = rancher_api_client.clusters.explore(harvester_mgmt_cluster['id'])
        spec = cluster_api.projects.Spec()
        spec.project_quota.cpu_limit = 5000
        spec.project_quota.mem_limit = 5000
        spec.namespace_quota.cpu_limit = self.ns_quota['cpu']
        spec.namespace_quota.mem_limit = self.ns_quota['mem']

        code, data = cluster_api.projects.create(unique_name, spec)
        assert 201 == code and unique_name == data['name'], (code, data)

        project_quota = data['resourceQuota']['limit']
        ns_quota = data['namespaceDefaultResourceQuota']['limit']
        assert project_quota['limitsCpu'] == spec.project_quota.cpu_limit
        assert project_quota['limitsMemory'] == spec.project_quota.mem_limit
        assert ns_quota['limitsCpu'] == spec.namespace_quota.cpu_limit
        assert ns_quota['limitsMemory'] == spec.namespace_quota.mem_limit

    @pytest.mark.dependency(name="create_namespace", depends=["create_project"])
    def test_create_namespace_on_project(
        self, api_client, rancher_api_client, unique_name, harvester_mgmt_cluster, wait_timeout
    ):
        cluster_api = rancher_api_client.clusters.explore(harvester_mgmt_cluster['id'])
        code, data = cluster_api.projects.get_by_name(unique_name)
        assert 200 == code, (code, data)

        proj_spec = cluster_api.projects.Spec.from_dict(data)
        proj_id = data['id'].split(':')[-1]
        labels = {"field.cattle.io/projectId": proj_id}
        annotations = {"field.cattle.io/projectId": data['id']}
        ns_mgr = cluster_api.imitate(api_client.namespaces)
        code, data = ns_mgr.create(unique_name, labels=labels, annotations=annotations)
        assert 201 == code, (code, data)

        # Check the data first to avoid race condition
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        found_quota = False
        while endtime > datetime.now():
            code, data = ns_mgr.get(unique_name)
            assert 200 == code, (code, data)
            if 'field.cattle.io/resourceQuota' in data.get('metadata', {}).get('annotations', {}):
                found_quota = True
                break

            sleep(3)

        assert found_quota, (
            f"Timeout waiting for resourceQuota annotation "
            f"in namespace {unique_name}. Data: {data}")
        
        ns_quota = loads(data['metadata']['annotations']['field.cattle.io/resourceQuota'])['limit']
        assert ns_quota['limitsCpu'] == proj_spec.namespace_quota.cpu_limit
        assert ns_quota['limitsMemory'] == proj_spec.namespace_quota.mem_limit

    @pytest.mark.negative
    @pytest.mark.dependency(name="decrease_quota", depends=["create_namespace"])
    def test_decrease_quota_when_vm_used(
        self, api_client, rancher_api_client, unique_name, vm_checker,
        unset_cpu_memory_overcommit, harvester_mgmt_cluster, ubuntu_image
    ):
        # ref: https://github.com/harvester/tests/issues/832
        cpu = int(self.ns_quota['cpu'] / 1000 - 1)
        mem = int(self.ns_quota['mem'] / 1000 - 1)
        vm = api_client.vms.Spec(cpu, mem)
        vm.add_image("disk-0", ubuntu_image['id'])
        code, data = api_client.vms.create(unique_name, vm, namespace=unique_name)
        assert 201 == code, (code, data)
        vm_started, (code, vmi) = vm_checker.wait_started(unique_name, namespace=unique_name)
        assert vm_started, (code, vmi)

        cluster_api = rancher_api_client.clusters.explore(harvester_mgmt_cluster['id'])
        ns_mgr = cluster_api.imitate(api_client.namespaces)
        code, data = ns_mgr.get(unique_name)
        assert 200 == code, (code, data)

        ns_quota = loads(data['metadata']['annotations']['field.cattle.io/resourceQuota'])['limit']
        ns_quota['limitsCpu'] = f"{(cpu -1) * 1000}m"
        anno = {'field.cattle.io/resourceQuota': dumps({"limit": ns_quota})}
        rancher_api_client.set_retries(status_forcelist=(502, 504))
        code, data = ns_mgr.update(unique_name, dict(annotations=anno))
        assert 500 == code and "is lower than the current used" in data['message'], (code, data)
        rancher_api_client.set_retries()

    @pytest.mark.dependency(depends=["decrease_quota"])
    def test_migrate_vm_when_exceed_quota(
        self, api_client, unique_name, vm_checker, available_node_names
    ):
        # ref: https://github.com/harvester/tests/issues/741
        if len(available_node_names) < 2:
            pytest.skip("Require 2+ nodes for migration testing.")

        is_running, ctx = vm_checker.wait_status_running(unique_name, namespace=unique_name)
        assert is_running, ctx
        code, vmi = api_client.vms.get_status(unique_name, unique_name)
        src_host = vmi['status']['nodeName']
        dst_host = next(n for n in available_node_names if n != src_host)

        vm_migrated, (code, data) = vm_checker.wait_migrated(
            unique_name, dst_host, namespace=unique_name
        )
        assert vm_migrated, (
            f"Failed to Migrate VM({unique_name}) from {src_host} to {dst_host}\n"
            f"API Status({code}): {data}"
        )

    @pytest.mark.dependency(depends=["decrease_quota"])
    def test_delete_project_when_vm_on_it(
        self, api_client, rancher_api_client, unique_name, vm_checker, harvester_mgmt_cluster
    ):
        cluster_api = rancher_api_client.clusters.explore(harvester_mgmt_cluster['id'])
        code, data = cluster_api.projects.get_by_name(unique_name)
        assert 200 == code, (code, data)

        code, data = cluster_api.projects.delete(data['id'])
        assert 200 == code and "removing" in data['state'], (code, data)

        code, data = api_client.vms.get(unique_name, unique_name)
        assert 200 == code and 'Running' in data['status']['printableStatus'], (code, data)

    @pytest.mark.dependency(depends=["decrease_quota"])
    def test_delete_namespace_when_vm_on_it(
        self, api_client, unique_name, wait_timeout
    ):
        # check VM is available
        code, data = api_client.vms.get(unique_name, unique_name)
        assert 200 == code, (code, data)

        code, data = api_client.namespaces.delete(unique_name)

        assert 200 == code, (code, data)
        assert "Terminating" == data['status']['phase']

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            status_code, data = api_client.namespaces.get(unique_name)
            if 404 == status_code:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"The namespace {unique_name} still not be deleted after {wait_timeout}s"
            )

        # check VM be deleted
        code, data = api_client.vms.get(unique_name, unique_name)
        assert 404 == code, (
            f"The VM {unique_name} still available in the namespace {unique_name}"
            " after the namespace be deleted.\n"
            f"Status({code}): {data}"
        )


@pytest.mark.p0
@pytest.mark.rancher
@pytest.mark.rke2
@pytest.mark.usefixtures("rke2_cluster")
class TestRKE2:
    @pytest.mark.dependency(depends=["import_harvester"], name="create_rke2")
    def test_create_rke2(self, rancher_api_client, unique_name, harvester_mgmt_cluster,
                         harvester_cloud_credential, rke2_cluster, ubuntu_image, vlan_network,
                         rancher_wait_timeout, polling_for):
        # Create Harvester kubeconfig for this RKE2 cluster
        code, data = rancher_api_client.kube_configs.create(
            rke2_cluster['name'],
            harvester_mgmt_cluster['id']
        )
        assert 200 == code, (
            f"Failed to create harvester kubeconfig for rke2 with error: {code}, {data}"
        )
        assert "" != data, (
            f"Harvester kubeconfig for rke2 should not be empty: {code}, {data}"
        )
        kubeconfig = data

        # Create credential for this RKE2 cluster
        code, data = rancher_api_client.secrets.create(
            name=unique_name,
            data={
                "credential": kubeconfig[1:-1].replace("\\n", "\n")
            },
            annotations={
                "v2prov-secret-authorized-for-cluster": rke2_cluster['name'],
                "v2prov-authorized-secret-deletes-on-cluster-removal": "true"
            }
        )
        assert 201 == code, (
            f"Failed to create secret with error: {code}, {data}"
        )
        cloud_provider_config_id = f"{data['metadata']['namespace']}:{data['metadata']['name']}"

        # Create RKE2 cluster spec
        code, data = rancher_api_client.harvester_configs.create(
            name=unique_name,
            cpus="2",
            mems="4",
            disks="40",
            image_id=ubuntu_image['id'],
            network_id=vlan_network['name'],
            ssh_user=ubuntu_image['ssh_user'],
            user_data=(
                "#cloud-config\n"
                "password: test\n"
                "chpasswd:\n"
                "    expire: false\n"
                "ssh_pwauth: true\n"
            ),
        )
        assert 201 == code, (
            f"Failed to create harvester config with error: {code}, {data}"
        )

        # Create RKE2 cluster
        code, data = rancher_api_client.mgmt_clusters.create(
            name=rke2_cluster['name'],
            cloud_provider_config_id=cloud_provider_config_id,
            hostname_prefix=f"{rke2_cluster['name']}-",
            harvester_config_name=unique_name,
            k8s_version=rke2_cluster['k8s_version'],
            cloud_credential_id=harvester_cloud_credential['id'],
            quantity=rke2_cluster['machine_count']
        )
        assert 201 == code, (
            f"Failed to create RKE2 MgmtCluster {unique_name} with error: {code}, {data}"
        )

        code, data = polling_for(
            f"cluster {rke2_cluster['name']} to be ready",
            lambda code, data:
                "active" == data['metadata']['state']['name'] and
                "Ready" in data['metadata']['state']['message'],
            rancher_api_client.mgmt_clusters.get, rke2_cluster['name'],
            timeout=rancher_wait_timeout
        )

        # update fixture value
        rke2_cluster['id'] = data["status"]["clusterName"]

        # Check deployments
        testees = ["harvester-cloud-provider", "harvester-csi-driver-controllers"]
        polling_for(
            f"harvester deployments on {rke2_cluster['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke2_cluster['id'], "kube-system", testees
        )

    @pytest.mark.dependency(depends=["create_rke2"])
    def test_create_pvc(self, rancher_api_client, harvester_mgmt_cluster,
                        unique_name, polling_for):
        cluster_id = harvester_mgmt_cluster['id']
        capi = rancher_api_client.clusters.explore(cluster_id)

        # Create PVC
        size = "1Gi"
        spec = capi.pvcs.Spec(size)
        code, data = capi.pvcs.create(unique_name, spec)
        assert 201 == code, (code, data)

        # Verify PVC is created
        code, data = polling_for(
            f"PVC {unique_name} to be in Bound phase",
            lambda code, data: "Bound" == data['status'].get('phase'),
            capi.pvcs.get, unique_name
        )

        # Verify the PV for created PVC
        pv_code, pv_data = capi.pvs.get(data['spec']['volumeName'])
        assert 200 == pv_code, (
            f"Relevant PV is NOT available for created PVC's PV({data['spec']['volumeName']})\n"
            f"Response data of PV: {data}"
        )

        # Verify size of the PV is aligned to requested size of PVC
        assert size == pv_data['spec']['capacity']['storage'], (
            "Size of the PV is NOT aligned to requested size of PVC,"
            f" expected: {size}, PV's size: {pv_data['spec']['capacity']['storage']}\n"
            f"Response data of PV: {data}"
        )

        # Verify PVC's size
        created_spec = capi.pvcs.Spec.from_dict(data)
        assert size == spec.size, (
            f"Size is NOT correct in created PVC, expected: {size}, created: {spec.size}\n"
            f"Response data: {data}"
        )

        # Verify the storage class exists
        sc_code, sc_data = capi.scs.get(created_spec.storage_cls)
        assert 200 == sc_code, (
            f"Storage Class is NOT exists for created PVC\n"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # verify the storage class is marked `default`
        assert 'true' == sc_data['metadata']['annotations'][capi.scs.DEFAULT_KEY], (
            f"Storage Class is NOT the DEFAULT for created PVC\n"
            f"Requested Storage Class: {spec.storage_cls!r}"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # teardown
        capi.pvcs.delete(unique_name)

    @pytest.mark.dependency(depends=["create_rke2"], name="csi_deployment")
    def test_csi_deployment(self, rancher_api_client, rke2_cluster, csi_deployment, polling_for):
        # create pvc
        code, data = rancher_api_client.pvcs.create(rke2_cluster['id'], csi_deployment['pvc'])
        assert 201 == code, (
            f"Fail to create {csi_deployment['pvc']} on {rke2_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"PVC {csi_deployment['pvc']} to be ready",
            lambda code, data:
                200 == code and
                "bound" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.pvcs.get, rke2_cluster['id'], csi_deployment['pvc']
        )

        # deployment with csi
        code, data = rancher_api_client.cluster_deployments.create(
            rke2_cluster['id'], csi_deployment['namespace'],
            csi_deployment['name'], csi_deployment['image'], csi_deployment['pvc']
        )
        assert 201 == code, (
            f"Fail to deploy {csi_deployment['name']} on {rke2_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke2_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

    @pytest.mark.dependency(depends=["csi_deployment"])
    def test_delete_deployment(self, rancher_api_client, rke2_cluster, csi_deployment,
                               polling_for):
        code, data = rancher_api_client.cluster_deployments.delete(
            rke2_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )
        assert 204 == code, (
            f"Failed to delete deployment {csi_deployment['name']} with error: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be deleted",
            lambda code, data:
                code == 404,
            rancher_api_client.cluster_deployments.get,
                rke2_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

        # teardown
        rancher_api_client.pvcs.delete(rke2_cluster['id'], csi_deployment['pvc'])

    @pytest.mark.dependency(depends=["create_rke2"], name="deploy_nginx")
    def test_deploy_nginx(self, rancher_api_client, rke2_cluster, nginx_deployment, polling_for):
        code, data = rancher_api_client.cluster_deployments.create(
            rke2_cluster['id'], nginx_deployment['namespace'],
            nginx_deployment['name'], nginx_deployment['image']
        )
        assert 201 == code, (
            f"Fail to deploy {nginx_deployment['name']} on {rke2_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {nginx_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke2_cluster['id'], nginx_deployment['namespace'], nginx_deployment['name']
        )

    @pytest.mark.dependency(depends=["deploy_nginx"])
    def test_load_balancer_service(self, rancher_api_client, rke2_cluster, nginx_deployment,
                                   lb_service, polling_for):
        # create LB service
        code, data = rancher_api_client.cluster_services.create(
            rke2_cluster['id'], lb_service["data"]
        )
        assert 201 == code, (
            f"Fail to create {lb_service['name']} for {nginx_deployment['name']}\n"
            f"API Response: {code}, {data}"
        )

        # check service active
        code, data = polling_for(
            f"service {lb_service['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_services.get, rke2_cluster['id'], lb_service['name']
        )

        # check Nginx can be queired via LB
        try:
            ingress = data["status"]["loadBalancer"]["ingress"][0]
            ingress_url = f"http://{ingress['ip']}:{ingress['ports'][0]['port']}"
        except Exception as e:
            raise AssertionError(
                f"Fail to get ingress info from {lb_service['name']}\n"
                f"Got error: {e}\n"
                f"Service data: {data}"
            )
        resp = rancher_api_client.session.get(ingress_url)
        assert resp.ok and "Welcome to nginx" in resp.text, (
            f"Fail to query load balancer {lb_service['name']}\n"
            f"Got error: {resp.status_code}, {resp.text}\n"
            f"Service data: {data}"
        )

        # teardown
        rancher_api_client.cluster_services.delete(rke2_cluster['id'], lb_service["name"])

    @pytest.mark.dependency(depends=["create_rke2"])
    def test_delete_rke2(self, api_client, rancher_api_client, rke2_cluster,
                         rancher_wait_timeout, polling_for):
        code, data = rancher_api_client.mgmt_clusters.delete(rke2_cluster['name'])
        assert 200 == code, (
            f"Failed to delete RKE2 MgmtCluster {rke2_cluster['name']} with error: {code}, {data}"
        )

        polling_for(
            f"cluster {rke2_cluster['name']} to be deleted",
            lambda code, data: 404 == code,
            rancher_api_client.mgmt_clusters.get, rke2_cluster['name'],
            timeout=rancher_wait_timeout
        )

        code, data = api_client.vms.get()
        remaining_vm_cnt = 0
        for d in data.get('data', []):
            vm_name = d.get('metadata', {}).get('name', "")
            if vm_name.startswith(f"{rke2_cluster['name']}-"):
                remaining_vm_cnt += 1
        assert 0 == remaining_vm_cnt, (f"Still have {remaining_vm_cnt} RKE2 VMs")


@pytest.mark.p0
@pytest.mark.rancher
@pytest.mark.rke1
@pytest.mark.usefixtures("rke1_cluster")
class TestRKE1:
    @pytest.mark.dependency(depends=["import_harvester"], name="create_rke1")
    def test_create_rke1(self, rancher_api_client, unique_name, harvester_mgmt_cluster,
                         rancher_wait_timeout,
                         rke1_cluster, harvester_cloud_credential,
                         ubuntu_image, vlan_network, polling_for):
        code, data = rancher_api_client.kube_configs.create(
            rke1_cluster['name'],
            harvester_mgmt_cluster['id']
        )
        assert 200 == code, f"Failed to create harvester kubeconfig with error: {code}, {data}"
        assert data.strip(), f"Harvester kubeconfig should not be empty: {code}, {data}"
        kubeconfig = data

        code, data = rancher_api_client.node_templates.create(
            name=unique_name,
            cpus=2,
            mems=4,
            disks=40,
            image_id=ubuntu_image['id'],
            network_id=vlan_network['name'],
            ssh_user=ubuntu_image['ssh_user'],
            cloud_credential_id=harvester_cloud_credential['id'],
            user_data=(
                "#cloud-config\n"
                "password: test\n"
                "chpasswd:\n"
                "    expire: false\n"
                "ssh_pwauth: true\n"
            ),
        )
        assert 201 == code, (
            f"Failed to create NodeTemplate {unique_name} with error: {code}, {data}"
        )

        node_template_id = data['id']

        code, data = rancher_api_client.clusters.create(
            rke1_cluster['name'], rke1_cluster['k8s_version'], kubeconfig
        )
        assert 201 == code, (
            f"Failed to create cluster {rke1_cluster['name']} with error: {code}, {data}"
        )

        # update fixture value
        rke1_cluster['id'] = data['id']

        # check cluster created and ready for use
        polling_for(
            f"cluster {rke1_cluster['name']} to be ready",
            lambda code, data:
                200 == code and
                "RKESecretsMigrated" in [c['type'] for c in data['conditions']],
            rancher_api_client.clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )

        code, data = rancher_api_client.node_pools.create(
            cluster_id=rke1_cluster['id'],
            node_template_id=node_template_id,
            hostname_prefix=f"{rke1_cluster['name']}-",
            quantity=rke1_cluster['machine_count']
        )
        assert 201 == code, (
            f"Failed to create NodePools for cluster {rke1_cluster['name']}\n"
            f"API Status({code}): {data}"
        )

        polling_for(
            f"MgmtCluster {rke1_cluster['name']} to be ready",
            lambda code, data: code == 200 and data.get('status', {}).get('ready', False),
            rancher_api_client.mgmt_clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )

    @pytest.mark.dependency(depends=["create_rke1"])
    def test_create_pvc(self, rancher_api_client, harvester_mgmt_cluster,
                        unique_name, polling_for):
        cluster_id = harvester_mgmt_cluster['id']
        capi = rancher_api_client.clusters.explore(cluster_id)

        # Create PVC
        size = "1Gi"
        spec = capi.pvcs.Spec(size)
        code, data = capi.pvcs.create(unique_name, spec)
        assert 201 == code, (code, data)

        # Verify PVC is created
        code, data = polling_for(
            f"PVC {unique_name} to be in Bound phase",
            lambda code, data: "Bound" == data['status'].get('phase'),
            capi.pvcs.get, unique_name
        )

        # Verify the PV for created PVC
        pv_code, pv_data = capi.pvs.get(data['spec']['volumeName'])
        assert 200 == pv_code, (
            f"Relevant PV is NOT available for created PVC's PV({data['spec']['volumeName']})\n"
            f"Response data of PV: {data}"
        )

        # Verify size of the PV is aligned to requested size of PVC
        assert size == pv_data['spec']['capacity']['storage'], (
            "Size of the PV is NOT aligned to requested size of PVC,"
            f" expected: {size}, PV's size: {pv_data['spec']['capacity']['storage']}\n"
            f"Response data of PV: {data}"
        )

        # Verify PVC's size
        created_spec = capi.pvcs.Spec.from_dict(data)
        assert size == spec.size, (
            f"Size is NOT correct in created PVC, expected: {size}, created: {spec.size}\n"
            f"Response data: {data}"
        )

        # Verify the storage class exists
        sc_code, sc_data = capi.scs.get(created_spec.storage_cls)
        assert 200 == sc_code, (
            f"Storage Class is NOT exists for created PVC\n"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # verify the storage class is marked `default`
        assert 'true' == sc_data['metadata']['annotations'][capi.scs.DEFAULT_KEY], (
            f"Storage Class is NOT the DEFAULT for created PVC\n"
            f"Requested Storage Class: {spec.storage_cls!r}"
            f"Created PVC Spec: {data}\n"
            f"SC Status({sc_code}): {sc_data}"
        )

        # teardown
        capi.pvcs.delete(unique_name)

    # harvester-cloud-provider
    @pytest.mark.dependency(depends=["create_rke1"], name="cloud_provider_chart")
    def test_cloud_provider_chart(self, rancher_api_client, rke1_cluster, polling_for):
        chart, deployment = "harvester-cloud-provider", "harvester-cloud-provider"
        polling_for(
            f"chart {chart} to be create",
            lambda code, data:
                201 == code,
            rancher_api_client.charts.create,
                rke1_cluster['id'], "kube-system", chart,
            timeout=60
        )
        # Polling on creation for possible 500 error in Rancher Apps
        # * https://github.com/rancher/rancher/issues/37610
        # * https://github.com/rancher/rancher/issues/43036

        polling_for(
            f"chart {chart} to be ready",
            lambda code, data:
                200 == code and
                "deployed" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.charts.get,
                rke1_cluster['id'], "kube-system", chart
        )
        polling_for(
            f"deployment {deployment} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], "kube-system", deployment
        )

    @pytest.mark.dependency(depends=["cloud_provider_chart"], name="deploy_nginx")
    def test_deploy_nginx(self, rancher_api_client, rke1_cluster, nginx_deployment, polling_for):
        code, data = rancher_api_client.cluster_deployments.create(
            rke1_cluster['id'], nginx_deployment['namespace'],
            nginx_deployment['name'], nginx_deployment['image']
        )
        assert 201 == code, (
            f"Fail to deploy {nginx_deployment['name']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {nginx_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], nginx_deployment['namespace'], nginx_deployment['name']
        )

    @pytest.mark.dependency(depends=["deploy_nginx"])
    def test_load_balancer_service(self, rancher_api_client, rke1_cluster, nginx_deployment,
                                   lb_service, polling_for):
        # create LB service
        code, data = rancher_api_client.cluster_services.create(
            rke1_cluster['id'], lb_service["data"]
        )
        assert 201 == code, (
            f"Fail to create {lb_service['name']} for {nginx_deployment['name']}\n"
            f"API Response: {code}, {data}"
        )

        # check service active
        code, data = polling_for(
            f"service {lb_service['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_services.get, rke1_cluster['id'], lb_service['name']
        )

        # check Nginx can be queired via LB
        try:
            ingress_ip = data["status"]["loadBalancer"]["ingress"][0]['ip']
            ingress_port = data['spec']['ports'][0]['port']
            ingress_url = f"http://{ingress_ip}:{ingress_port}"
        except Exception as e:
            raise AssertionError(
                f"Fail to get ingress info from {lb_service['name']}\n"
                f"Got error: {e}\n"
                f"Service data: {data}"
            )
        resp = rancher_api_client.session.get(ingress_url)
        assert resp.ok and "Welcome to nginx" in resp.text, (
            f"Fail to query load balancer {lb_service['name']}\n"
            f"Got error: {resp.status_code}, {resp.text}\n"
            f"Service data: {data}"
        )

        # teardown
        rancher_api_client.cluster_services.delete(rke1_cluster['id'], lb_service["name"])

    # harvester-csi-driver
    @pytest.mark.dependency(depends=["create_rke1"], name="csi_driver_chart")
    def test_csi_driver_chart(self, rancher_api_client, rke1_cluster, polling_for):
        chart, deployment = "harvester-csi-driver", "harvester-csi-driver-controllers"
        polling_for(
            f"chart {chart} to be create",
            lambda code, data:
                201 == code,
            rancher_api_client.charts.create,
                rke1_cluster['id'], "kube-system", chart,
            timeout=60
        )
        # Polling on creation for possible 500 error in Rancher Apps
        # * https://github.com/rancher/rancher/issues/37610
        # * https://github.com/rancher/rancher/issues/43036

        polling_for(
            f"chart {chart} to be ready",
            lambda code, data:
                200 == code and
                "deployed" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.charts.get,
                rke1_cluster['id'], "kube-system", chart
        )
        polling_for(
            f"deployment {deployment} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], "kube-system", deployment
        )

    @pytest.mark.dependency(depends=["csi_driver_chart"], name="csi_deployment")
    def test_csi_deployment(self, rancher_api_client, rke1_cluster, csi_deployment, polling_for):
        # create pvc
        code, data = rancher_api_client.pvcs.create(rke1_cluster['id'], csi_deployment['pvc'])
        assert 201 == code, (
            f"Fail to create {csi_deployment['pvc']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"PVC {csi_deployment['pvc']} to be ready",
            lambda code, data:
                200 == code and
                "bound" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.pvcs.get, rke1_cluster['id'], csi_deployment['pvc']
        )

        # deployment with csi
        code, data = rancher_api_client.cluster_deployments.create(
            rke1_cluster['id'], csi_deployment['namespace'],
            csi_deployment['name'], csi_deployment['image'], csi_deployment['pvc']
        )
        assert 201 == code, (
            f"Fail to deploy {csi_deployment['name']} on {rke1_cluster['name']}\n"
            f"API Response: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be ready",
            lambda code, data:
                200 == code and
                "active" == data.get("metadata", {}).get("state", {}).get("name"),
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

    @pytest.mark.dependency(depends=["csi_deployment"])
    def test_delete_deployment(self, rancher_api_client, rke1_cluster, csi_deployment,
                               polling_for):
        code, data = rancher_api_client.cluster_deployments.delete(
            rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )
        assert 204 == code, (
            f"Failed to delete deployment {csi_deployment['name']} with error: {code}, {data}"
        )

        polling_for(
            f"deployment {csi_deployment['name']} to be deleted",
            lambda code, data:
                code == 404,
            rancher_api_client.cluster_deployments.get,
                rke1_cluster['id'], csi_deployment['namespace'], csi_deployment['name']
        )

        # teardown
        rancher_api_client.pvcs.delete(rke1_cluster['id'], csi_deployment['pvc'])

    @pytest.mark.dependency(depends=["create_rke1"])
    def test_delete_rke1(self, api_client, rancher_api_client, rke1_cluster,
                         rancher_wait_timeout, polling_for):
        code, data = rancher_api_client.mgmt_clusters.delete(rke1_cluster['id'])
        assert 200 == code, (
            f"Failed to delete RKE2 MgmtCluster {rke1_cluster['name']} with error: {code}, {data}"
        )

        def _remaining_vm_cnt() -> int:
            # in RKE1, when the cluster is deleted, VMs may still in Terminating status
            code, data = api_client.vms.get()
            remaining_vm_cnt = 0
            for d in data.get('data', []):
                vm_name = d.get('metadata', {}).get('name', "")
                if vm_name.startswith(f"{rke1_cluster['name']}-"):
                    remaining_vm_cnt += 1
            return remaining_vm_cnt

        polling_for(
            f"cluster {rke1_cluster['name']} to be deleted",
            lambda code, data: code == 404 and _remaining_vm_cnt() == 0,
            rancher_api_client.clusters.get, rke1_cluster['id'],
            timeout=rancher_wait_timeout
        )
