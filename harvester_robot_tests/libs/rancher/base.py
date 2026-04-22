"""
Base class for Rancher Integration operations
Defines the interface for both CRD and REST implementations
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Rancher Integration implementations"""

    # Harvester Management Cluster Operations
    @abstractmethod
    def create_harvester_mgmt_cluster(self, cluster_name):
        """Create Harvester management cluster entry in Rancher (Import Existing)"""
        pass

    @abstractmethod
    def get_harvester_mgmt_cluster(self, cluster_name):
        """Get Harvester management cluster details"""
        pass

    @abstractmethod
    def delete_harvester_mgmt_cluster(self, cluster_name):
        """Delete Harvester management cluster entry"""
        pass

    @abstractmethod
    def wait_for_cluster_id(self, cluster_name, timeout):
        """
        Wait for cluster to get its internal ID (status.clusterName).
        This appears shortly after cluster creation, before registration.
        """
        pass

    @abstractmethod
    def wait_for_harvester_ready(self, cluster_name, timeout):
        """
        Wait for Harvester cluster to be active and ready in Rancher.
        This happens after setting the registration URL.
        """
        pass

    # Cluster Registration Operations
    @abstractmethod
    def get_cluster_registration_url(self, cluster_id, rancher_endpoint, timeout=300):
        """Get cluster registration URL for importing Harvester"""
        pass

    @abstractmethod
    def set_cluster_registration_url(self, url):
        """Set cluster-registration-url setting in Harvester"""
        pass

    # Version Operations
    @abstractmethod
    def get_all_rke2_versions(self, rancher_endpoint, max_versions=None):
        """
        Get all available RKE2 versions from Rancher.

        Args:
            rancher_endpoint: Rancher server endpoint
            max_versions: Maximum number of versions to return (None = all)

        Returns:
            List of version strings sorted by semantic version (newest first)
        """
        pass

    @abstractmethod
    def get_rke2_version(self, target_version):
        """
        Get RKE2 version from Rancher that matches target version.

        Args:
            target_version: Target version prefix (e.g. 'v1.28', 'v1.29')

        Returns:
            Full version string (e.g. 'v1.28.15+rke2r1')
        """
        pass

    # Cloud Credential Operations
    @abstractmethod
    def create_cloud_credential(self, name, kubeconfig, cluster_id):
        """Create cloud credential for Harvester"""
        pass

    @abstractmethod
    def get_cloud_credential(self, credential_id):
        """Get cloud credential details"""
        pass

    @abstractmethod
    def delete_cloud_credential(self, credential_id):
        """Delete cloud credential"""
        pass

    # RKE2 Cluster Operations
    @abstractmethod
    def create_rke2_cluster(self, name, cloud_provider_config_id, hostname_prefix,
                            harvester_config_name, k8s_version, cloud_credential_id,
                            quantity, ingress):
        """Create RKE2 cluster on Harvester"""
        pass

    @abstractmethod
    def get_rke2_cluster(self, cluster_name):
        """Get RKE2 cluster details"""
        pass

    @abstractmethod
    def delete_rke2_cluster(self, cluster_name):
        """Delete RKE2 cluster"""
        pass

    @abstractmethod
    def wait_for_rke2_cluster_ready(self, cluster_name, timeout):
        """Wait for RKE2 cluster to be ready"""
        pass

    @abstractmethod
    def wait_for_rke2_cluster_deleted(self, cluster_name, timeout):
        """Wait for RKE2 cluster to be deleted"""
        pass

    @abstractmethod
    def scale_rke2_cluster(self, cluster_name, worker_count, harvester_config_name):
        """Scale RKE2 cluster by adding/removing a worker-only machine pool.

        Args:
            cluster_name: Name of the RKE2 cluster
            worker_count: Number of worker nodes (0 to remove worker pool)
            harvester_config_name: HarvesterConfig name for worker pool nodes
        """
        pass

    @abstractmethod
    def upgrade_rke2_cluster(self, cluster_name, new_k8s_version):
        """Upgrade RKE2 cluster to a new Kubernetes version.

        Args:
            cluster_name: Name of the RKE2 cluster
            new_k8s_version: Target Kubernetes version string
        """
        pass

    # Harvester Config Operations
    @abstractmethod
    def create_harvester_config(self, name, cpus, mems, disks, image_id,
                                network_id, ssh_user, user_data):
        """Create Harvester config for RKE2 node template"""
        pass

    # Kubeconfig Operations
    @abstractmethod
    def generate_kubeconfig(self, cluster_id, cluster_name):
        """Generate full-access kubeconfig for a cluster"""
        pass

    @abstractmethod
    def generate_cloud_provider_kubeconfig(self, cluster_id, cluster_name):
        """Generate cloud provider kubeconfig with external URL"""
        pass

    # Secret Operations
    @abstractmethod
    def create_secret(self, name, data, annotations):
        """Create secret for cloud provider config"""
        pass

    # Deployment Operations
    @abstractmethod
    def create_deployment(self, cluster_id, namespace, name, image, pvc=None,
                          command=None):
        """Create deployment in guest cluster"""
        pass

    @abstractmethod
    def get_deployment(self, cluster_id, namespace, name):
        """Get deployment details"""
        pass

    @abstractmethod
    def delete_deployment(self, cluster_id, namespace, name):
        """Delete deployment"""
        pass

    @abstractmethod
    def wait_for_deployment_ready(self, cluster_id, namespace, name, timeout):
        """Wait for deployment to be ready"""
        pass

    @abstractmethod
    def wait_for_deployment_deleted(self, cluster_id, namespace, name, timeout):
        """Wait for deployment to be deleted"""
        pass

    # PVC Operations
    @abstractmethod
    def create_pvc(self, cluster_id, name, size="1Gi", storage_class=None):
        """Create PVC in guest cluster"""
        pass

    @abstractmethod
    def get_pvc(self, cluster_id, name):
        """Get PVC details"""
        pass

    @abstractmethod
    def delete_pvc(self, cluster_id, name):
        """Delete PVC"""
        pass

    @abstractmethod
    def wait_for_pvc_bound(self, cluster_id, name, timeout):
        """Wait for PVC to be bound"""
        pass

    # Load Balancer Service Operations
    @abstractmethod
    def create_lb_service(self, cluster_id, service_data):
        """Create LoadBalancer service"""
        pass

    @abstractmethod
    def get_lb_service(self, cluster_id, name):
        """Get LoadBalancer service details"""
        pass

    @abstractmethod
    def delete_lb_service(self, cluster_id, name):
        """Delete LoadBalancer service"""
        pass

    @abstractmethod
    def wait_for_lb_service_ready(self, cluster_id, name, timeout):
        """Wait for LoadBalancer service to be ready"""
        pass

    @abstractmethod
    def query_lb_service(self, url, retries=10, interval=5):
        """Query LoadBalancer service endpoint with retries"""
        pass

    @abstractmethod
    def query_lb_via_proxy(self, cluster_id, service_name, port=8080,
                           namespace="default", retries=10, interval=5):
        """Query LoadBalancer service via Rancher's k8s service proxy"""
        pass

    # Harvester Deployments Check
    @abstractmethod
    def wait_for_harvester_deployments_ready(self, cluster_id, timeout):
        """Wait for harvester-cloud-provider and harvester-csi-driver to be ready"""
        pass

    # VLAN Network Operations
    @abstractmethod
    def create_vlan_network(self, name, vlan_id, cluster_network):
        """Create VLAN network"""
        pass

    @abstractmethod
    def delete_vlan_network(self, name):
        """Delete VLAN network"""
        pass

    # IP Pool Operations
    @abstractmethod
    def get_ip_pool(self, name):
        """Get IP pool by name, returns None if not found"""
        pass

    @abstractmethod
    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """Create IP pool"""
        pass

    @abstractmethod
    def delete_ip_pool(self, name):
        """Delete IP pool"""
        pass

    # Image Operations
    @abstractmethod
    def create_image(self, name, url):
        """Create image by URL"""
        pass

    @abstractmethod
    def wait_for_image_ready(self, name, timeout):
        """Wait for image to be ready"""
        pass

    @abstractmethod
    def delete_image(self, name):
        """Delete image"""
        pass

    # Import Existing Cluster Operations
    @abstractmethod
    def create_import_cluster(self, name):
        """Create a minimal provisioning cluster for importing an existing cluster.

        Unlike RKE2 provisioning or custom clusters, this creates a cluster
        with an empty spec. The actual cluster is running externally and the
        Rancher agent is applied to it via the registration manifest URL.

        Args:
            name: Cluster name
        """
        pass

    @abstractmethod
    def wait_for_import_cluster_ready(self, cluster_name, timeout):
        """Wait for an imported cluster to become active in Rancher.

        Checks status.ready and Updated/Provisioned conditions.
        Unlike wait_for_rke2_cluster_ready, this does NOT check
        machinePools or cluster.x-k8s.io machines (imported clusters
        have none).

        Args:
            cluster_name: Name of the provisioning cluster
            timeout: Timeout in seconds
        """
        pass

    # Custom RKE2 Cluster Operations
    @abstractmethod
    def create_custom_rke2_cluster(self, name, cloud_provider_config_id,
                                   k8s_version, cloud_credential_id,
                                   ingress="traefik"):
        """Create a custom RKE2 cluster without machinePools.

        The cluster uses the Harvester cloud provider but nodes are
        registered externally via the registration command.

        Args:
            name: Cluster name
            cloud_provider_config_id: Cloud provider config secret ID
            k8s_version: Kubernetes version
            cloud_credential_id: Cloud credential ID
            ingress: Ingress controller (default: traefik)
        """
        pass

    @abstractmethod
    def update_cluster_chart_name(self, cluster_name, mgmt_cluster_id):
        """Update the cloud provider clusterName in a custom cluster's chartValues.

        For custom clusters, the management cluster ID (c-m-xxxxx) is not
        known at creation time. This patches the provisioning cluster spec
        so the cloud provider can correctly identify VMs belonging to this
        cluster.

        Args:
            cluster_name: Provisioning cluster name
            mgmt_cluster_id: Management cluster ID (e.g. c-m-xxxxx)
        """
        pass

    @abstractmethod
    def fix_cloud_provider_cluster_name(self, cluster_id):
        """Fix the cloud-provider --cluster-name arg on the guest cluster.

        Rancher deploys the chart with the provisioning name instead of
        the management cluster ID. This patches the deployment's arg
        directly and waits for the rollout to complete.

        Args:
            cluster_id: Management cluster ID (e.g. c-m-xxxxx)
        """
        pass

    @abstractmethod
    def get_cluster_registration_command(self, cluster_name, timeout):
        """Get the node registration command for a custom cluster.

        Args:
            cluster_name: Name of the provisioning cluster
            timeout: Timeout in seconds

        Returns:
            str: The insecure node command to run on VMs
        """
        pass

    # Harvester VM Operations (for custom cluster nodes)
    @abstractmethod
    def create_harvester_vm(self, name, image_id, network_id, cpus, memory,
                            disk_size, ssh_user, user_data, network_data="",
                            guest_cluster_id=""):
        """Create a VM on Harvester.

        Args:
            name: VM name
            image_id: Image ID (namespace/name format)
            network_id: Network ID (namespace/name format)
            cpus: Number of CPU cores
            memory: Memory size in GiB
            disk_size: Disk size in GiB
            ssh_user: SSH username
            user_data: Cloud-init user data string
            network_data: Cloud-init network data string (optional)
            guest_cluster_id: Management cluster ID (c-m-xxxxx) for LB
                labels. When set, adds harvesterhci.io/creator and
                guestcluster.harvesterhci.io/name labels so the
                Harvester LB webhook can discover the VMs.
        """
        pass

    @abstractmethod
    def wait_for_harvester_vm_ready(self, name, timeout):
        """Wait for a Harvester VM to be running.

        Args:
            name: VM name
            timeout: Timeout in seconds
        """
        pass

    @abstractmethod
    def delete_harvester_vm(self, name):
        """Delete a Harvester VM and its associated volume.

        Args:
            name: VM name
        """
        pass

    @abstractmethod
    def install_chart(self, cluster_id, repo_name, chart_name, version,
                      release_name, namespace, values=None):
        """Install a Helm chart on a guest cluster via Rancher catalog API."""
        pass

    @abstractmethod
    def create_cluster_repo(self, cluster_id, repo_name, git_url, git_branch):
        """Create a ClusterRepo on a guest cluster."""
        pass

    @abstractmethod
    def wait_for_cluster_repo_ready(self, cluster_id, repo_name, timeout):
        """Wait for a ClusterRepo to finish downloading on a guest cluster."""
        pass

    @abstractmethod
    def get_chart_versions(self, repo_name, chart_name, cluster_id=None):
        """Get available versions for a chart from a Rancher chart repo."""
        pass

    @abstractmethod
    def create_cloud_config_secret(self, cluster_id, secret_name,
                                   namespace, kubeconfig):
        """Create a cloud-provider-config secret on a guest cluster."""
        pass

    @abstractmethod
    def wait_for_chart_app_ready(self, cluster_id, release_name,
                                 namespace, timeout):
        """Wait for a chart app to be deployed and ready."""
        pass
