"""
Rancher Keywords - creates Rancher() instance and delegates - NO direct API calls!
Layer 3: Keyword wrappers for Robot Framework
"""
import os
import sys
from datetime import datetime

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utility.utility import logging, generate_name_with_suffix  # noqa E402
from rancher import Rancher  # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG, DEFAULT_RKE2_USER_DATA, DEFAULT_RKE2_NODE_CPUS, DEFAULT_RKE2_NODE_MEMORY, DEFAULT_RKE2_NODE_DISK  # noqa E402


class rancher_keywords:
    """Rancher keyword wrapper - creates Rancher component and delegates"""

    def __init__(self):
        """Initialize rancher keywords with lazy loading"""
        self._rancher = None
        self._state = {}

    @property
    def rancher(self):
        """Lazy initialize rancher to allow API client setup first"""
        if self._rancher is None:
            self._rancher = Rancher()
        return self._rancher

    def generate_unique_name(self, prefix="test"):
        """
        Generate unique name with timestamp

        Args:
            prefix: Prefix for the name

        Returns:
            str: Unique name with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        name = f"{prefix}-{timestamp}"
        logging(f"Generated unique name: {name}")
        return name

    # State Management
    def set_state(self, key, value):
        """Store state for later use between keywords"""
        self._state[key] = value
        logging(f"Set state {key} = {value}")

    def get_state(self, key, default=None):
        """Retrieve stored state"""
        return self._state.get(key, default)

    def clear_state(self, key=None):
        """Clear state - either specific key or all"""
        if key:
            self._state.pop(key, None)
        else:
            self._state.clear()

    # Harvester Management Cluster Operations
    def create_harvester_mgmt_cluster(self, cluster_name):
        """
        Create Harvester management cluster entry in Rancher (Import Existing)

        Args:
            cluster_name: Name of the cluster entry to create

        Returns:
            dict: Cluster data
        """
        logging(f"Creating Harvester management cluster: {cluster_name}")
        return self.rancher.create_harvester_mgmt_cluster(cluster_name)

    def get_harvester_mgmt_cluster(self, cluster_name):
        """
        Get Harvester management cluster details

        Args:
            cluster_name: Name of the cluster

        Returns:
            dict: Cluster data or None if not found
        """
        logging(f"Getting Harvester management cluster: {cluster_name}")
        return self.rancher.get_harvester_mgmt_cluster(cluster_name)

    def delete_harvester_mgmt_cluster(self, cluster_name):
        """
        Delete Harvester management cluster entry

        Args:
            cluster_name: Name of the cluster to delete
        """
        logging(f"Deleting Harvester management cluster: {cluster_name}")
        self.rancher.delete_harvester_mgmt_cluster(cluster_name)

    def wait_for_cluster_id(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for cluster to get its internal ID (status.clusterName)

        Args:
            cluster_name: Name of the cluster
            timeout: Timeout in seconds

        Returns:
            dict: Cluster data with ID
        """
        logging(f"Waiting for cluster {cluster_name} to get cluster ID")
        return self.rancher.wait_for_cluster_id(cluster_name, timeout)

    def wait_for_harvester_ready(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for Harvester cluster to be ready in Rancher

        Args:
            cluster_name: Name of the cluster
            timeout: Timeout in seconds

        Returns:
            dict: Cluster data when ready
        """
        logging(f"Waiting for Harvester cluster {cluster_name} to be ready")
        return self.rancher.wait_for_harvester_ready(cluster_name, int(timeout))

    # Import Harvester Operations
    def get_cluster_registration_url(self, cluster_id, rancher_endpoint, timeout=DEFAULT_TIMEOUT):
        """
        Get cluster registration URL for importing Harvester

        Args:
            cluster_id: Internal cluster ID (e.g. c-m-xxxxx)
            rancher_endpoint: Rancher server endpoint
            timeout: Timeout in seconds

        Returns:
            str: Registration manifest URL
        """
        logging(f"Getting cluster registration URL for: {cluster_id}")
        return self.rancher.get_cluster_registration_url(cluster_id, rancher_endpoint, timeout)

    def set_cluster_registration_url(self, url):
        """
        Set cluster-registration-url setting in Harvester

        Args:
            url: Registration URL to set
        """
        logging("Setting cluster-registration-url")
        self.rancher.set_cluster_registration_url(url)

    def get_all_rke2_versions(self, rancher_endpoint, max_versions=None):
        """
        Get all available RKE2 versions from Rancher

        Args:
            rancher_endpoint: Rancher server endpoint
            max_versions: Maximum number of versions to return (None = all)

        Returns:
            list: List of RKE2 version strings sorted newest first
        """
        logging("Getting all RKE2 versions from Rancher")
        max_ver = int(max_versions) if max_versions else None
        versions = self.rancher.get_all_rke2_versions(rancher_endpoint, max_ver)
        self.set_state('all_rke2_versions', versions)
        return versions

    def resolve_rke2_versions(self, versions_input, rancher_endpoint, max_versions=10):
        """
        Resolve RKE2 versions based on input specification.

        Handles special values:
        - "all": Get all available versions from Rancher (limited by max_versions)
        - "latest": Get only the latest version
        - "v1.28,v1.29": Get latest version matching each prefix
        - "v1.28.15+rke2r1": Use specific version as-is

        Args:
            versions_input: Version specification string
            rancher_endpoint: Rancher server endpoint
            max_versions: Max versions when using "all"

        Returns:
            list: List of resolved version strings
        """
        logging(f"Resolving RKE2 versions from input: {versions_input}")

        if not versions_input or versions_input.lower() == 'all':
            # Get all available versions
            versions = self.get_all_rke2_versions(rancher_endpoint, max_versions)
            logging(f"Resolved 'all' to {len(versions)} versions")
            return versions

        if versions_input.lower() == 'latest':
            # Get only the latest version
            versions = self.get_all_rke2_versions(rancher_endpoint, 1)
            logging(f"Resolved 'latest' to: {versions[0]}")
            return versions

        # Handle comma-separated version prefixes
        result_versions = []
        for ver_input in versions_input.split(','):
            ver_input = ver_input.strip()
            if not ver_input:
                continue

            # If it's a full version (contains +), use as-is
            if '+' in ver_input:
                result_versions.append(ver_input)
                logging(f"Using specified version: {ver_input}")
            else:
                # It's a prefix, resolve to matching version
                full_version = self.get_rke2_version(ver_input, rancher_endpoint)
                result_versions.append(full_version)

        logging(f"Resolved to {len(result_versions)} versions: {result_versions}")
        return result_versions

    def get_rke2_version(self, target_version, rancher_endpoint):
        """
        Get RKE2 version from Rancher that matches target version

        Args:
            target_version: Target version prefix (e.g. 'v1.28')
            rancher_endpoint: Rancher server endpoint

        Returns:
            str: Full RKE2 version (e.g. 'v1.28.15+rke2r1')
        """
        logging(f"Getting RKE2 version for target: {target_version}")
        version = self.rancher.get_rke2_version(target_version, rancher_endpoint)
        self.set_state('rke2_version', version)
        return version

    def import_harvester_to_rancher(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Full workflow to import Harvester to Rancher

        Args:
            cluster_name: Name for the Harvester entry in Rancher
            timeout: Timeout for the import operation

        Returns:
            dict: Harvester cluster data
        """
        logging(f"Importing Harvester to Rancher as: {cluster_name}")

        # Create Harvester entry in Rancher
        self.create_harvester_mgmt_cluster(cluster_name)

        # Wait for cluster to get registration URL
        cluster = self.wait_for_harvester_ready(cluster_name, timeout)
        cluster_id = cluster.get("status", {}).get("clusterName", "")

        # Get registration URL
        manifest_url = self.get_cluster_registration_url(cluster_id)

        # Set registration URL in Harvester
        self.set_cluster_registration_url(manifest_url)

        # Wait for cluster to become ready
        return self.wait_for_harvester_ready(cluster_name, timeout)

    # Cloud Credential Operations
    def create_cloud_credential(self, name, kubeconfig, cluster_id):
        """
        Create cloud credential for Harvester

        Args:
            name: Name for the credential
            kubeconfig: Kubeconfig content
            cluster_id: Harvester cluster ID

        Returns:
            dict: Credential data
        """
        logging(f"Creating cloud credential: {name}")
        return self.rancher.create_cloud_credential(name, kubeconfig, cluster_id)

    def delete_cloud_credential(self, credential_id):
        """
        Delete cloud credential

        Args:
            credential_id: ID of the credential to delete
        """
        logging(f"Deleting cloud credential: {credential_id}")
        self.rancher.delete_cloud_credential(credential_id)

    # RKE2 Cluster Operations
    def create_rke2_cluster(self, name, cloud_provider_config_id, hostname_prefix,
                            harvester_config_name, k8s_version, cloud_credential_id,
                            quantity=1, ingress="traefik"):
        """
        Create RKE2 cluster on Harvester

        Args:
            name: Cluster name
            cloud_provider_config_id: Cloud provider config secret ID
            hostname_prefix: Prefix for node hostnames
            harvester_config_name: Harvester config name
            k8s_version: Kubernetes version
            cloud_credential_id: Cloud credential ID
            quantity: Number of nodes (default: 1)
            ingress: Ingress controller to use

        Returns:
            dict: Cluster data
        """
        logging(f"Creating RKE2 cluster: {name}")
        return self.rancher.create_rke2_cluster(
            name, cloud_provider_config_id, hostname_prefix,
            harvester_config_name, k8s_version, cloud_credential_id,
            int(quantity), ingress
        )

    def get_rke2_cluster(self, cluster_name):
        """
        Get RKE2 cluster details

        Args:
            cluster_name: Name of the cluster

        Returns:
            dict: Cluster data or None if not found
        """
        logging(f"Getting RKE2 cluster: {cluster_name}")
        return self.rancher.get_rke2_cluster(cluster_name)

    def delete_rke2_cluster(self, cluster_name):
        """
        Delete RKE2 cluster

        Args:
            cluster_name: Name of the cluster to delete
        """
        logging(f"Deleting RKE2 cluster: {cluster_name}")
        self.rancher.delete_rke2_cluster(cluster_name)

    def wait_for_rke2_cluster_ready(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for RKE2 cluster to be ready

        Args:
            cluster_name: Name of the cluster
            timeout: Timeout in seconds

        Returns:
            dict: Cluster data when ready
        """
        logging(f"Waiting for RKE2 cluster {cluster_name} to be ready")
        return self.rancher.wait_for_rke2_cluster_ready(cluster_name, int(timeout))

    def wait_for_rke2_cluster_deleted(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for RKE2 cluster to be deleted

        Args:
            cluster_name: Name of the cluster
            timeout: Timeout in seconds

        Returns:
            bool: True when deleted
        """
        logging(f"Waiting for RKE2 cluster {cluster_name} to be deleted")
        return self.rancher.wait_for_rke2_cluster_deleted(cluster_name, int(timeout))

    def scale_rke2_cluster(self, cluster_name, worker_count, harvester_config_name):
        """
        Scale RKE2 cluster by adding/removing a worker-only machine pool.

        Args:
            cluster_name: Name of the RKE2 cluster
            worker_count: Number of worker nodes (0 to remove worker pool)
            harvester_config_name: HarvesterConfig name for worker pool nodes
        """
        logging(f"Scaling RKE2 cluster {cluster_name}: worker_count={worker_count}")
        self.rancher.scale_rke2_cluster(cluster_name, int(worker_count), harvester_config_name)

    def upgrade_rke2_cluster(self, cluster_name, new_k8s_version):
        """
        Upgrade RKE2 cluster to a new Kubernetes version.

        Args:
            cluster_name: Name of the RKE2 cluster
            new_k8s_version: Target Kubernetes version string
        """
        logging(f"Upgrading RKE2 cluster {cluster_name} to {new_k8s_version}")
        self.rancher.upgrade_rke2_cluster(cluster_name, new_k8s_version)

    def get_next_rke2_version(self, current_version, rancher_endpoint):
        """
        Get the latest RKE2 version in the next minor stream.

        Only minor version upgrades are supported (e.g. v1.34 -> v1.35).

        Args:
            current_version: Current RKE2 version (e.g. 'v1.34.5+rke2r1')
            rancher_endpoint: Rancher server endpoint

        Returns:
            str: Next version string, or empty string if none available
        """
        logging(f"Looking for next RKE2 minor version after {current_version}")
        from pkg_resources import parse_version

        all_versions = self.rancher.get_all_rke2_versions(rancher_endpoint)

        current_base = current_version.split("+")[0]  # e.g. v1.34.5
        parts = current_base.lstrip("v").split(".")
        if len(parts) < 2:
            logging(f"Cannot parse minor version from {current_version}")
            return ""

        current_minor = int(parts[1])
        next_minor_prefix = f"v{parts[0]}.{current_minor + 1}."

        candidates = []
        for v in all_versions:
            v_base = v.split("+")[0]
            if v_base.startswith(next_minor_prefix):
                candidates.append((parse_version(v_base), v))

        if not candidates:
            logging(f"No version found in next minor stream ({next_minor_prefix}) "
                    f"for {current_version}")
            return ""

        # Return the latest patch in the next minor stream
        candidates.sort(key=lambda x: x[0], reverse=True)
        next_version = candidates[0][1]
        logging(f"Found next RKE2 version: {next_version}")
        return next_version

    def verify_lb_response(self, url, expected_text=None):
        """
        Verify LoadBalancer is responding with expected content.

        Args:
            url: URL to query
            expected_text: Text expected in response (optional, any 200 OK passes if None)

        Returns:
            bool: True if response matches
        """
        logging(f"Verifying LB response from: {url}")
        code, text = self.rancher.query_lb_service(url)
        if code == 200:
            if expected_text and expected_text not in text:
                raise Exception(f"Expected '{expected_text}' in response, got: {text[:200]}")
            logging("LB response verified successfully")
            return True
        raise Exception(f"Expected 200 OK, got: {code}, {text[:200]}")

    def verify_lb_via_cluster(self, cluster_id, service_name, port=8080,
                              namespace="default", expected_text=None):
        """
        Verify LoadBalancer service via Rancher's Kubernetes service proxy.

        Uses /k8s/clusters/{id}/api/v1/namespaces/{ns}/services/{svc}:{port}/proxy/
        which works regardless of whether the LB VIP is routable from the test runner.

        Args:
            cluster_id: Downstream cluster ID (e.g. c-m-xxxxx)
            service_name: Name of the LoadBalancer service
            port: Service port (default 8080)
            namespace: Service namespace (default: default)
            expected_text: Text expected in response (optional)

        Returns:
            bool: True if response matches
        """
        logging(f"Verifying LB {service_name} via Rancher proxy (cluster {cluster_id})")
        code, text = self.rancher.query_lb_via_proxy(
            cluster_id, service_name, port, namespace)
        if code == 200:
            if expected_text and expected_text not in str(text):
                raise Exception(
                    f"Expected '{expected_text}' in response, got: {str(text)[:200]}")
            logging("LB response verified successfully via proxy")
            return True
        raise Exception(f"Expected 200 OK via proxy, got: {code}, {str(text)[:200]}")

    # Harvester Config Operations
    def create_harvester_config(self, name, cpus=None, mems=None, disks=None, image_id="",
                                network_id="", ssh_user="ubuntu", user_data=None):
        """
        Create Harvester config for RKE2 node template

        Args:
            name: Config name
            cpus: Number of CPUs (default: DEFAULT_RKE2_NODE_CPUS)
            mems: Memory in GB (default: DEFAULT_RKE2_NODE_MEMORY)
            disks: Disk size in GB (default: DEFAULT_RKE2_NODE_DISK)
            image_id: Image ID to use
            network_id: Network name
            ssh_user: SSH user (default: ubuntu)
            user_data: Cloud-init user data

        Returns:
            dict: Config data
        """
        if not cpus:
            cpus = DEFAULT_RKE2_NODE_CPUS
        if not mems:
            mems = DEFAULT_RKE2_NODE_MEMORY
        if not disks:
            disks = DEFAULT_RKE2_NODE_DISK
        if not user_data:
            user_data = DEFAULT_RKE2_USER_DATA
        logging(f"Creating Harvester config: {name}")
        return self.rancher.create_harvester_config(
            name, int(cpus), int(mems), int(disks),
            image_id, network_id, ssh_user, user_data
        )

    # Kubeconfig Operations
    def generate_kubeconfig(self, cluster_id, cluster_name):
        """
        Generate full-access kubeconfig for a cluster (for cloud credentials)

        Args:
            cluster_id: Cluster ID
            cluster_name: Cluster name

        Returns:
            str: Kubeconfig content
        """
        logging(f"Generating kubeconfig for cluster: {cluster_name}")
        return self.rancher.generate_kubeconfig(cluster_id, cluster_name)

    def generate_cloud_provider_kubeconfig(self, cluster_id, cluster_name):
        """
        Generate cloud provider kubeconfig with external URL (for cloud provider secret)

        Args:
            cluster_id: Cluster ID
            cluster_name: Cluster name

        Returns:
            str: Kubeconfig content with external Rancher URL
        """
        logging(f"Generating cloud provider kubeconfig for cluster: {cluster_name}")
        return self.rancher.generate_cloud_provider_kubeconfig(cluster_id, cluster_name)

    # Secret Operations
    def create_cloud_provider_secret(self, name, kubeconfig, cluster_name):
        """
        Create secret for cloud provider config

        Args:
            name: Secret name
            kubeconfig: Kubeconfig content
            cluster_name: Cluster name for annotations

        Returns:
            dict: Secret data
        """
        logging(f"Creating cloud provider secret: {name}")
        annotations = {
            "v2prov-secret-authorized-for-cluster": cluster_name,
            "v2prov-authorized-secret-deletes-on-cluster-removal": "true"
        }
        data = {"credential": kubeconfig.replace("\\n", "\n")}
        return self.rancher.create_secret(name, data, annotations)

    # Deployment Operations
    def create_deployment(self, cluster_id, namespace, name, image, pvc=None):
        """
        Create deployment in guest cluster

        Args:
            cluster_id: Cluster ID
            namespace: Namespace
            name: Deployment name
            image: Container image
            pvc: PVC name to mount (optional)

        Returns:
            dict: Deployment data
        """
        logging(f"Creating deployment {name} in cluster {cluster_id}")
        return self.rancher.create_deployment(cluster_id, namespace, name, image, pvc)

    def delete_deployment(self, cluster_id, namespace, name):
        """
        Delete deployment from guest cluster

        Args:
            cluster_id: Cluster ID
            namespace: Namespace
            name: Deployment name
        """
        logging(f"Deleting deployment {name} from cluster {cluster_id}")
        self.rancher.delete_deployment(cluster_id, namespace, name)

    def wait_for_deployment_ready(self, cluster_id, namespace, name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for deployment to be ready

        Args:
            cluster_id: Cluster ID
            namespace: Namespace
            name: Deployment name
            timeout: Timeout in seconds

        Returns:
            dict: Deployment data when ready
        """
        logging(f"Waiting for deployment {name} to be ready")
        return self.rancher.wait_for_deployment_ready(
            cluster_id, namespace, name, int(timeout)
        )

    def wait_for_deployment_deleted(self, cluster_id, namespace, name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for deployment to be deleted

        Args:
            cluster_id: Cluster ID
            namespace: Namespace
            name: Deployment name
            timeout: Timeout in seconds

        Returns:
            bool: True when deleted
        """
        logging(f"Waiting for deployment {name} to be deleted")
        return self.rancher.wait_for_deployment_deleted(
            cluster_id, namespace, name, int(timeout)
        )

    # PVC Operations
    def create_pvc(self, cluster_id, name, size="1Gi", storage_class=None):
        """
        Create PVC in guest cluster

        Args:
            cluster_id: Cluster ID
            name: PVC name
            size: Storage size (default: 1Gi)
            storage_class: Storage class name (optional)

        Returns:
            dict: PVC data
        """
        logging(f"Creating PVC {name} in cluster {cluster_id}")
        return self.rancher.create_pvc(cluster_id, name, size, storage_class)

    def delete_pvc(self, cluster_id, name):
        """
        Delete PVC from guest cluster

        Args:
            cluster_id: Cluster ID
            name: PVC name
        """
        logging(f"Deleting PVC {name} from cluster {cluster_id}")
        self.rancher.delete_pvc(cluster_id, name)

    def wait_for_pvc_bound(self, cluster_id, name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for PVC to be bound

        Args:
            cluster_id: Cluster ID
            name: PVC name
            timeout: Timeout in seconds

        Returns:
            dict: PVC data when bound
        """
        logging(f"Waiting for PVC {name} to be bound")
        return self.rancher.wait_for_pvc_bound(cluster_id, name, int(timeout))

    # Load Balancer Service Operations
    def create_lb_service(self, cluster_id, namespace, name, target_deployment,
                          port=8080, target_port=80, ipam="dhcp"):
        """
        Create LoadBalancer service

        Args:
            cluster_id: Cluster ID
            namespace: Namespace
            name: Service name
            target_deployment: Deployment to target
            port: Service port (default: 8080)
            target_port: Target port (default: 80)
            ipam: IPAM mode - 'dhcp' or 'pool' (default: dhcp)

        Returns:
            dict: Service data
        """
        logging(f"Creating LoadBalancer service {name} in cluster {cluster_id}")

        service_data = {
            "type": "service",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": {
                    "cloudprovider.harvesterhci.io/ipam": ipam
                }
            },
            "spec": {
                "type": "LoadBalancer",
                "sessionAffinity": None,
                "ports": [
                    {
                        "name": "http",
                        "port": int(port),
                        "protocol": "TCP",
                        "targetPort": int(target_port)
                    }
                ],
                "selector": {
                    "name": target_deployment
                }
            }
        }

        return self.rancher.create_lb_service(cluster_id, service_data)

    def delete_lb_service(self, cluster_id, name):
        """
        Delete LoadBalancer service

        Args:
            cluster_id: Cluster ID
            name: Service name
        """
        logging(f"Deleting LoadBalancer service {name} from cluster {cluster_id}")
        self.rancher.delete_lb_service(cluster_id, name)

    def wait_for_lb_service_ready(self, cluster_id, name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for LoadBalancer service to be ready

        Args:
            cluster_id: Cluster ID
            name: Service name
            timeout: Timeout in seconds

        Returns:
            dict: Service data when ready
        """
        logging(f"Waiting for LoadBalancer service {name} to be ready")
        return self.rancher.wait_for_lb_service_ready(cluster_id, name, int(timeout))

    def query_lb_service(self, url):
        """
        Query LoadBalancer service endpoint

        Args:
            url: URL to query

        Returns:
            tuple: (status_code, response_text)
        """
        logging(f"Querying LoadBalancer service at: {url}")
        return self.rancher.query_lb_service(url)

    def verify_lb_nginx_response(self, url):
        """
        Verify LoadBalancer returns nginx welcome page

        Args:
            url: URL to query

        Returns:
            bool: True if nginx welcome page found
        """
        logging(f"Verifying nginx response from: {url}")
        code, text = self.rancher.query_lb_service(url)
        if code == 200 and "Welcome to nginx" in text:
            logging("Nginx welcome page verified")
            return True
        raise Exception(f"Expected nginx welcome page, got: {code}, {text}")

    # Harvester Deployments Check
    def wait_for_harvester_deployments_ready(self, cluster_id, timeout=DEFAULT_TIMEOUT):
        """
        Wait for harvester-cloud-provider and harvester-csi-driver to be ready

        Args:
            cluster_id: Cluster ID
            timeout: Timeout in seconds
        """
        logging(f"Waiting for Harvester deployments in cluster {cluster_id}")
        self.rancher.wait_for_harvester_deployments_ready(cluster_id, int(timeout))

    # VLAN Network Operations
    def create_vlan_network(self, name, vlan_id, cluster_network):
        """
        Create VLAN network

        Args:
            name: Network name
            vlan_id: VLAN ID
            cluster_network: Cluster network name

        Returns:
            dict: Network data
        """
        logging(f"Creating VLAN network: {name}")
        return self.rancher.create_vlan_network(name, vlan_id, cluster_network)

    def delete_vlan_network(self, name):
        """
        Delete VLAN network

        Args:
            name: Network name
        """
        logging(f"Deleting VLAN network: {name}")
        self.rancher.delete_vlan_network(name)

    # IP Pool Operations
    def get_ip_pool(self, name):
        """
        Get IP pool by name

        Args:
            name: IP pool name

        Returns:
            dict: IP pool data, or None if not found
        """
        logging(f"Getting IP pool: {name}")
        return self.rancher.get_ip_pool(name)

    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """
        Create IP pool

        Args:
            name: IP pool name
            subnet: Subnet CIDR
            start_ip: Start IP address
            end_ip: End IP address
            network_id: Network ID

        Returns:
            dict: IP pool data
        """
        logging(f"Creating IP pool: {name}")
        return self.rancher.create_ip_pool(name, subnet, start_ip, end_ip, network_id)

    def delete_ip_pool(self, name):
        """
        Delete IP pool

        Args:
            name: IP pool name
        """
        logging(f"Deleting IP pool: {name}")
        self.rancher.delete_ip_pool(name)

    # Image Operations
    def create_image(self, name, url):
        """
        Create image by URL

        Args:
            name: Image name
            url: URL to download image from

        Returns:
            dict: Image data
        """
        logging(f"Creating image: {name}")
        return self.rancher.create_image(name, url)

    def wait_for_image_ready(self, name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for image to be ready

        Args:
            name: Image name
            timeout: Timeout in seconds

        Returns:
            dict: Image data when ready
        """
        logging(f"Waiting for image {name} to be ready")
        return self.rancher.wait_for_image_ready(name, int(timeout))

    def delete_image(self, name):
        """
        Delete image

        Args:
            name: Image name
        """
        logging(f"Deleting image: {name}")
        self.rancher.delete_image(name)
