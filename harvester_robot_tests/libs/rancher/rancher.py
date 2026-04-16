"""
Rancher Component - delegates to CRD or REST implementation
Layer 4: Selects implementation based on strategy

The implementation is selected based on the HARVESTER_OPERATION_STRATEGY
environment variable. Valid values are 'crd' or 'rest'. Defaults to 'crd' if not set.
"""

import os
from constant import HarvesterOperationStrategy
from rancher.rest import Rest
from rancher.crd import CRD
from rancher.base import Base


class Rancher(Base):
    """
    Rancher component that delegates to CRD or REST implementation

    The implementation is selected based on:
    - HARVESTER_OPERATION_STRATEGY environment variable ('crd' or 'rest')
    - Defaults to 'crd' if not set
    """

    def __init__(self):
        """Initialize Rancher component"""
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.rancher = CRD()
        else:
            self.rancher = Rest()

    # Harvester Management Cluster Operations
    def create_harvester_mgmt_cluster(self, cluster_name):
        """Create Harvester management cluster entry in Rancher (Import Existing)"""
        return self.rancher.create_harvester_mgmt_cluster(cluster_name)

    def get_harvester_mgmt_cluster(self, cluster_name):
        """Get Harvester management cluster details"""
        return self.rancher.get_harvester_mgmt_cluster(cluster_name)

    def delete_harvester_mgmt_cluster(self, cluster_name):
        """Delete Harvester management cluster entry"""
        return self.rancher.delete_harvester_mgmt_cluster(cluster_name)

    def wait_for_cluster_id(self, cluster_name, timeout):
        """Wait for cluster to get its internal ID"""
        return self.rancher.wait_for_cluster_id(cluster_name, timeout)

    def wait_for_harvester_ready(self, cluster_name, timeout):
        """Wait for Harvester cluster to be ready in Rancher"""
        return self.rancher.wait_for_harvester_ready(cluster_name, timeout)

    # Cluster Registration Operations
    def get_cluster_registration_url(self, cluster_id, rancher_endpoint, timeout=300):
        """Get cluster registration URL for importing Harvester"""
        return self.rancher.get_cluster_registration_url(cluster_id, rancher_endpoint, timeout)

    def set_cluster_registration_url(self, url):
        """Set cluster-registration-url setting in Harvester"""
        return self.rancher.set_cluster_registration_url(url)

    def get_all_rke2_versions(self, rancher_endpoint=None, max_versions=None):
        """Get all available RKE2 versions from Rancher"""
        return self.rancher.get_all_rke2_versions(rancher_endpoint, max_versions)

    def get_rke2_version(self, target_version, rancher_endpoint=None):
        """Get RKE2 version from Rancher that matches target version"""
        return self.rancher.get_rke2_version(target_version, rancher_endpoint)

    # Cloud Credential Operations
    def create_cloud_credential(self, name, kubeconfig, cluster_id):
        """Create cloud credential for Harvester"""
        return self.rancher.create_cloud_credential(name, kubeconfig, cluster_id)

    def get_cloud_credential(self, credential_id):
        """Get cloud credential details"""
        return self.rancher.get_cloud_credential(credential_id)

    def delete_cloud_credential(self, credential_id):
        """Delete cloud credential"""
        return self.rancher.delete_cloud_credential(credential_id)

    # RKE2 Cluster Operations
    def create_rke2_cluster(self, name, cloud_provider_config_id, hostname_prefix,
                            harvester_config_name, k8s_version, cloud_credential_id,
                            quantity, ingress):
        """Create RKE2 cluster on Harvester"""
        return self.rancher.create_rke2_cluster(
            name, cloud_provider_config_id, hostname_prefix,
            harvester_config_name, k8s_version, cloud_credential_id,
            quantity, ingress
        )

    def get_rke2_cluster(self, cluster_name):
        """Get RKE2 cluster details"""
        return self.rancher.get_rke2_cluster(cluster_name)

    def delete_rke2_cluster(self, cluster_name):
        """Delete RKE2 cluster"""
        return self.rancher.delete_rke2_cluster(cluster_name)

    def wait_for_rke2_cluster_ready(self, cluster_name, timeout):
        """Wait for RKE2 cluster to be ready"""
        return self.rancher.wait_for_rke2_cluster_ready(cluster_name, timeout)

    def wait_for_rke2_cluster_deleted(self, cluster_name, timeout):
        """Wait for RKE2 cluster to be deleted"""
        return self.rancher.wait_for_rke2_cluster_deleted(cluster_name, timeout)

    def scale_rke2_cluster(self, cluster_name, worker_count, harvester_config_name):
        """Scale RKE2 cluster by adding/removing a worker-only machine pool"""
        return self.rancher.scale_rke2_cluster(cluster_name, worker_count, harvester_config_name)

    def upgrade_rke2_cluster(self, cluster_name, new_k8s_version):
        """Upgrade RKE2 cluster to a new Kubernetes version"""
        return self.rancher.upgrade_rke2_cluster(cluster_name, new_k8s_version)

    # Harvester Config Operations
    def create_harvester_config(self, name, cpus, mems, disks, image_id,
                                network_id, ssh_user, user_data):
        """Create Harvester config for RKE2 node template"""
        return self.rancher.create_harvester_config(
            name, cpus, mems, disks, image_id, network_id, ssh_user, user_data
        )

    # Kubeconfig Operations
    def generate_kubeconfig(self, cluster_id, cluster_name):
        """Generate full-access kubeconfig for a cluster"""
        return self.rancher.generate_kubeconfig(cluster_id, cluster_name)

    def generate_cloud_provider_kubeconfig(self, cluster_id, cluster_name):
        """Generate cloud provider kubeconfig with external URL"""
        return self.rancher.generate_cloud_provider_kubeconfig(cluster_id, cluster_name)

    # Secret Operations
    def create_secret(self, name, data, annotations):
        """Create secret for cloud provider config"""
        return self.rancher.create_secret(name, data, annotations)

    # Deployment Operations
    def create_deployment(self, cluster_id, namespace, name, image, pvc=None):
        """Create deployment in guest cluster"""
        return self.rancher.create_deployment(cluster_id, namespace, name, image, pvc)

    def get_deployment(self, cluster_id, namespace, name):
        """Get deployment details"""
        return self.rancher.get_deployment(cluster_id, namespace, name)

    def delete_deployment(self, cluster_id, namespace, name):
        """Delete deployment"""
        return self.rancher.delete_deployment(cluster_id, namespace, name)

    def wait_for_deployment_ready(self, cluster_id, namespace, name, timeout):
        """Wait for deployment to be ready"""
        return self.rancher.wait_for_deployment_ready(cluster_id, namespace, name, timeout)

    def wait_for_deployment_deleted(self, cluster_id, namespace, name, timeout):
        """Wait for deployment to be deleted"""
        return self.rancher.wait_for_deployment_deleted(cluster_id, namespace, name, timeout)

    # PVC Operations
    def create_pvc(self, cluster_id, name, size="1Gi", storage_class=None):
        """Create PVC in guest cluster"""
        return self.rancher.create_pvc(cluster_id, name, size, storage_class)

    def get_pvc(self, cluster_id, name):
        """Get PVC details"""
        return self.rancher.get_pvc(cluster_id, name)

    def delete_pvc(self, cluster_id, name):
        """Delete PVC"""
        return self.rancher.delete_pvc(cluster_id, name)

    def wait_for_pvc_bound(self, cluster_id, name, timeout):
        """Wait for PVC to be bound"""
        return self.rancher.wait_for_pvc_bound(cluster_id, name, timeout)

    # Load Balancer Service Operations
    def create_lb_service(self, cluster_id, service_data):
        """Create LoadBalancer service"""
        return self.rancher.create_lb_service(cluster_id, service_data)

    def get_lb_service(self, cluster_id, name):
        """Get LoadBalancer service details"""
        return self.rancher.get_lb_service(cluster_id, name)

    def delete_lb_service(self, cluster_id, name):
        """Delete LoadBalancer service"""
        return self.rancher.delete_lb_service(cluster_id, name)

    def wait_for_lb_service_ready(self, cluster_id, name, timeout):
        """Wait for LoadBalancer service to be ready"""
        return self.rancher.wait_for_lb_service_ready(cluster_id, name, timeout)

    def query_lb_service(self, url, retries=10, interval=5):
        """Query LoadBalancer service endpoint with retries"""
        return self.rancher.query_lb_service(url, retries, interval)

    def query_lb_via_proxy(self, cluster_id, service_name, port=8080,
                           namespace="default", retries=10, interval=5):
        """Query LoadBalancer service via Rancher's k8s service proxy"""
        return self.rancher.query_lb_via_proxy(
            cluster_id, service_name, port, namespace, retries, interval)

    # Harvester Deployments Check
    def wait_for_harvester_deployments_ready(self, cluster_id, timeout):
        """Wait for harvester-cloud-provider and harvester-csi-driver to be ready"""
        return self.rancher.wait_for_harvester_deployments_ready(cluster_id, timeout)

    # Cluster Network Operations
    def create_cluster_network(self, name):
        """Create cluster network"""
        return self.rancher.create_cluster_network(name)

    def delete_cluster_network(self, name):
        """Delete cluster network"""
        return self.rancher.delete_cluster_network(name)

    def create_vlan_config(self, name, cluster_network, nic):
        """Create VLAN config to bind NIC to cluster network"""
        return self.rancher.create_vlan_config(name, cluster_network, nic)

    def delete_vlan_config(self, name):
        """Delete VLAN config"""
        return self.rancher.delete_vlan_config(name)

    def wait_for_cluster_network_ready(self, name, timeout=120):
        """Wait for cluster network to become ready"""
        return self.rancher.wait_for_cluster_network_ready(name, timeout)

    # VLAN Network Operations
    def create_vlan_network(self, name, vlan_id, cluster_network):
        """Create VLAN network"""
        return self.rancher.create_vlan_network(name, vlan_id, cluster_network)

    def delete_vlan_network(self, name):
        """Delete VLAN network"""
        return self.rancher.delete_vlan_network(name)

    # IP Pool Operations
    def get_ip_pool(self, name):
        """Get IP pool by name"""
        return self.rancher.get_ip_pool(name)

    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """Create IP pool"""
        return self.rancher.create_ip_pool(name, subnet, start_ip, end_ip, network_id)

    def delete_ip_pool(self, name):
        """Delete IP pool"""
        return self.rancher.delete_ip_pool(name)

    # Image Operations
    def create_image(self, name, url):
        """Create image by URL"""
        return self.rancher.create_image(name, url)

    def wait_for_image_ready(self, name, timeout):
        """Wait for image to be ready"""
        return self.rancher.wait_for_image_ready(name, timeout)

    def delete_image(self, name):
        """Delete image"""
        return self.rancher.delete_image(name)

    # Import Existing Cluster Operations
    def create_import_cluster(self, name):
        """Create a minimal provisioning cluster for import"""
        return self.rancher.create_import_cluster(name)

    def wait_for_import_cluster_ready(self, cluster_name, timeout):
        """Wait for an imported cluster to become active"""
        return self.rancher.wait_for_import_cluster_ready(
            cluster_name, timeout
        )

    # Custom RKE2 Cluster Operations
    def create_custom_rke2_cluster(self, name, cloud_provider_config_id,
                                   k8s_version, cloud_credential_id,
                                   ingress="traefik"):
        """Create a custom RKE2 cluster without machinePools"""
        return self.rancher.create_custom_rke2_cluster(
            name, cloud_provider_config_id, k8s_version,
            cloud_credential_id, ingress
        )

    def update_cluster_chart_name(self, cluster_name, mgmt_cluster_id):
        """Patch custom cluster's chartValues with the real management ID"""
        return self.rancher.update_cluster_chart_name(
            cluster_name, mgmt_cluster_id
        )

    def fix_cloud_provider_cluster_name(self, cluster_id):
        """Fix cloud-provider --cluster-name arg on the guest cluster"""
        return self.rancher.fix_cloud_provider_cluster_name(cluster_id)

    def get_cluster_registration_command(self, cluster_name, timeout):
        """Get the node registration command for a custom cluster"""
        return self.rancher.get_cluster_registration_command(
            cluster_name, timeout
        )

    # Harvester VM Operations (for custom cluster nodes)
    def create_harvester_vm(self, name, image_id, network_id, cpus, memory,
                            disk_size, ssh_user, user_data, network_data=""):
        """Create a VM on Harvester"""
        return self.rancher.create_harvester_vm(
            name, image_id, network_id, cpus, memory,
            disk_size, ssh_user, user_data, network_data
        )

    def wait_for_harvester_vm_ready(self, name, timeout):
        """Wait for a Harvester VM to be running"""
        return self.rancher.wait_for_harvester_vm_ready(name, timeout)

    def delete_harvester_vm(self, name):
        """Delete a Harvester VM"""
        return self.rancher.delete_harvester_vm(name)

    # Chart Install Operations
    def install_chart(self, cluster_id, repo_name, chart_name, version,
                      release_name, namespace, values=None):
        """Install a Helm chart on a guest cluster"""
        return self.rancher.install_chart(
            cluster_id, repo_name, chart_name, version,
            release_name, namespace, values
        )

    def create_cluster_repo(self, cluster_id, repo_name, git_url, git_branch):
        """Create a ClusterRepo on a guest cluster"""
        return self.rancher.create_cluster_repo(
            cluster_id, repo_name, git_url, git_branch
        )

    def wait_for_cluster_repo_ready(self, cluster_id, repo_name,
                                    timeout=600):
        """Wait for a ClusterRepo to finish downloading"""
        return self.rancher.wait_for_cluster_repo_ready(
            cluster_id, repo_name, timeout
        )

    def get_chart_versions(self, repo_name, chart_name, cluster_id=None):
        """Get available versions for a chart"""
        return self.rancher.get_chart_versions(
            repo_name, chart_name, cluster_id
        )

    def create_cloud_config_secret(self, cluster_id, secret_name,
                                   namespace, kubeconfig):
        """Create cloud-provider-config secret on guest cluster"""
        return self.rancher.create_cloud_config_secret(
            cluster_id, secret_name, namespace, kubeconfig
        )

    def wait_for_chart_app_ready(self, cluster_id, release_name,
                                 namespace, timeout):
        """Wait for chart app to be deployed"""
        return self.rancher.wait_for_chart_app_ready(
            cluster_id, release_name, namespace, timeout
        )
