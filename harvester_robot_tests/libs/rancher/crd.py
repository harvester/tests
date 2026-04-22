"""
Rancher CRD Implementation - Kubernetes API operations
Layer 4: Makes actual kubectl/K8s API calls for Rancher integration operations

This implementation uses kubectl commands against Rancher's Kubernetes API
for managing Rancher resources (clusters, etc.) via CRD approach.
"""

import os
import time
import subprocess
import json
import tempfile
import requests
import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException
from constant import (
    DEFAULT_TIMEOUT,
    DEFAULT_TIMEOUT_LONG,
    HARVESTER_API_GROUP,
    HARVESTER_API_VERSION,
    DEFAULT_NAMESPACE,
)
from utility.utility import logging, get_retry_count_and_interval
from rancher.base import Base


class CRD(Base):
    """
    CRD implementation for Rancher Integration operations using Kubernetes API

    This implementation uses kubectl against Rancher's Kubernetes API for
    managing Rancher resources (clusters, ClusterRegistrationTokens, etc.).

    For Harvester-local operations, it uses the default kubeconfig (Harvester).
    For Rancher operations, it generates a kubeconfig targeting Rancher's K8s API.
    """

    def __init__(self):
        """Initialize Kubernetes clients"""
        # Harvester K8s clients (for Harvester-local operations)
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.apps_api = client.AppsV1Api()

        # Harvester API groups
        self.harvester_group = HARVESTER_API_GROUP
        self.harvester_version = HARVESTER_API_VERSION

        # Rancher API groups (for kubectl commands against Rancher)
        self.rancher_mgmt_group = "management.cattle.io"
        self.rancher_mgmt_version = "v3"
        self.rancher_provisioning_group = "provisioning.cattle.io"
        self.rancher_provisioning_version = "v1"
        self.rancher_machine_config_group = "rke-machine-config.cattle.io"
        self.rancher_machine_config_version = "v1"

        # Rancher authentication
        self.rancher_token = None
        self.rancher_endpoint = None
        self._rancher_kubeconfig_path = None
        self._guest_kubeconfig_paths = {}

    def __del__(self):
        """Cleanup temporary kubeconfig files"""
        for path in [self._rancher_kubeconfig_path,
                     *self._guest_kubeconfig_paths.values()]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _get_rancher_credentials(self):
        """Get Rancher credentials from Robot variables or environment"""
        try:
            from robot.libraries.BuiltIn import BuiltIn
            endpoint = BuiltIn().get_variable_value("${RANCHER_ENDPOINT}", "")
            username = BuiltIn().get_variable_value("${RANCHER_USERNAME}", "admin")
            password = BuiltIn().get_variable_value("${RANCHER_PASSWORD}", "password1234")
        except Exception:
            endpoint = os.getenv("RANCHER_ENDPOINT", "")
            username = os.getenv("RANCHER_USERNAME", "admin")
            password = os.getenv("RANCHER_PASSWORD", "password1234")

        if not endpoint:
            raise Exception("RANCHER_ENDPOINT not configured")

        return endpoint, username, password

    def _authenticate_rancher(self):
        """Authenticate with Rancher and get API token"""
        if self.rancher_token:
            return self.rancher_token

        endpoint, username, password = self._get_rancher_credentials()
        self.rancher_endpoint = endpoint

        logging(f"Authenticating with Rancher at {endpoint} as user {username}")

        session = requests.Session()
        session.verify = False
        session.headers.update({"Content-Type": "application/json"})

        from urllib.parse import urljoin
        url = urljoin(endpoint, "v3-public/localProviders/local?action=login")

        response = session.post(url, json={"username": username, "password": password})

        if response.status_code != 201:
            logging(f"Auth failed - Status: {response.status_code}, Response: {response.text}")
            raise Exception(
                f"Failed to authenticate with Rancher: "
                f"{response.status_code} {response.text}"
            )

        token = response.json().get("token")
        if not token:
            raise Exception("No token in authentication response")

        self.rancher_token = token
        logging("Successfully authenticated with Rancher")
        return token

    def _get_rancher_kubeconfig(self):
        """
        Generate a kubeconfig file for accessing Rancher's Kubernetes API.

        Rancher exposes its K8s API at /k8s/clusters/local for the management cluster.
        We use the Rancher API token as bearer token for authentication.

        Returns:
            str: Path to temporary kubeconfig file
        """
        if self._rancher_kubeconfig_path and os.path.exists(self._rancher_kubeconfig_path):
            return self._rancher_kubeconfig_path

        # Ensure we have auth token
        token = self._authenticate_rancher()

        # Rancher's K8s API endpoint for the local/management cluster
        # This is where provisioning.cattle.io CRDs are managed
        k8s_endpoint = f"{self.rancher_endpoint.rstrip('/')}/k8s/clusters/local"

        # Generate kubeconfig content
        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": "rancher-local",
                "cluster": {
                    "server": k8s_endpoint,
                    "insecure-skip-tls-verify": True
                }
            }],
            "contexts": [{
                "name": "rancher-local",
                "context": {
                    "cluster": "rancher-local",
                    "user": "rancher-admin"
                }
            }],
            "current-context": "rancher-local",
            "users": [{
                "name": "rancher-admin",
                "user": {
                    "token": token
                }
            }]
        }

        # Write to temporary file
        fd, path = tempfile.mkstemp(suffix=".kubeconfig", prefix="rancher-")
        with os.fdopen(fd, 'w') as f:
            yaml.dump(kubeconfig, f)

        self._rancher_kubeconfig_path = path
        logging(f"Created Rancher kubeconfig at: {path}")
        return path

    def _run_kubectl_rancher(self, args, input_data=None):
        """
        Run kubectl command against Rancher's Kubernetes API.

        This uses a dynamically generated kubeconfig that targets Rancher's
        K8s API at /k8s/clusters/local with the Rancher API token.

        Args:
            args: List of kubectl arguments
            input_data: Optional stdin data to pipe to kubectl

        Returns:
            tuple: (return_code, stdout, stderr)
        """
        kubeconfig = self._get_rancher_kubeconfig()
        return self._run_kubectl(args, kubeconfig=kubeconfig, input_data=input_data, insecure=True)

    def _get_guest_kubeconfig(self, cluster_id):
        """Generate a kubeconfig for accessing a guest cluster via Rancher proxy.

        Same approach as _get_rancher_kubeconfig but targets
        /k8s/clusters/{cluster_id} instead of /k8s/clusters/local.

        Args:
            cluster_id: Rancher management cluster ID (e.g. c-m-xxxxx)

        Returns:
            str: Path to temporary kubeconfig file
        """
        if cluster_id in self._guest_kubeconfig_paths:
            path = self._guest_kubeconfig_paths[cluster_id]
            if os.path.exists(path):
                return path

        token = self._authenticate_rancher()
        k8s_endpoint = (f"{self.rancher_endpoint.rstrip('/')}"
                        f"/k8s/clusters/{cluster_id}")

        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": f"rancher-guest-{cluster_id}",
                "cluster": {
                    "server": k8s_endpoint,
                    "insecure-skip-tls-verify": True
                }
            }],
            "contexts": [{
                "name": f"rancher-guest-{cluster_id}",
                "context": {
                    "cluster": f"rancher-guest-{cluster_id}",
                    "user": "rancher-admin"
                }
            }],
            "current-context": f"rancher-guest-{cluster_id}",
            "users": [{
                "name": "rancher-admin",
                "user": {
                    "token": token
                }
            }]
        }

        fd, path = tempfile.mkstemp(
            suffix=".kubeconfig", prefix=f"guest-{cluster_id}-"
        )
        with os.fdopen(fd, 'w') as f:
            yaml.dump(kubeconfig, f)

        self._guest_kubeconfig_paths[cluster_id] = path
        logging(f"Created guest kubeconfig for {cluster_id}")
        return path

    def _run_kubectl_guest(self, cluster_id, args, input_data=None):
        """Run kubectl command against a guest cluster via Rancher proxy.

        Uses a dynamically generated kubeconfig that targets Rancher's
        K8s API at /k8s/clusters/{cluster_id}.

        NOTE: Do NOT use this for --raw requests. kubectl --raw strips the
        path component from the kubeconfig server URL, so requests go to
        the Rancher management cluster instead of the guest cluster.
        Use _run_kubectl_raw_guest for --raw API calls.

        Args:
            cluster_id: Rancher management cluster ID
            args: List of kubectl arguments
            input_data: Optional stdin data to pipe to kubectl

        Returns:
            tuple: (return_code, stdout, stderr)
        """
        kubeconfig = self._get_guest_kubeconfig(cluster_id)
        return self._run_kubectl(
            args, kubeconfig=kubeconfig, input_data=input_data, insecure=True
        )

    def _run_kubectl_raw_guest(self, cluster_id, raw_path, method="get",
                               input_data=None):
        """Run a kubectl --raw request against a guest cluster.

        kubectl --raw strips the path component from the kubeconfig server
        URL, so we use the Rancher management kubeconfig and prepend
        /k8s/clusters/{cluster_id} to the raw path ourselves.

        Args:
            cluster_id: Rancher management cluster ID
            raw_path: API path (e.g. /v1/catalog.cattle.io.clusterrepos/...)
            method: HTTP method — "get" or "create" (POST)
            input_data: Optional stdin data for POST requests

        Returns:
            tuple: (return_code, stdout, stderr)
        """
        full_path = f"/k8s/clusters/{cluster_id}{raw_path}"
        args = [method, "--raw", full_path]
        if method == "create" and input_data is not None:
            args.extend(["-f", "-"])
        return self._run_kubectl_rancher(args, input_data=input_data)

    def _run_kubectl(self, args, kubeconfig=None, context=None, input_data=None, insecure=False):
        """
        Run kubectl command and return output

        Args:
            args: List of kubectl arguments
            kubeconfig: Path to kubeconfig file (optional, uses default if not provided)
            context: Kubectl context to use (optional)
            input_data: Optional stdin data to pipe to kubectl
            insecure: Skip TLS certificate verification (for self-signed certs)

        Returns:
            tuple: (return_code, stdout, stderr)
        """
        cmd = ["kubectl"]
        if kubeconfig:
            cmd.extend(["--kubeconfig", kubeconfig])
        if context:
            cmd.extend(["--context", context])
        if insecure:
            cmd.append("--insecure-skip-tls-verify")
        cmd.extend(args)

        logging(f"Running kubectl command: {' '.join(cmd)}", level="DEBUG")
        result = subprocess.run(  # nosec B603
            cmd, capture_output=True, text=True, input=input_data
        )
        return result.returncode, result.stdout, result.stderr

    def create_harvester_mgmt_cluster(self, cluster_name):
        """
        Create Harvester management cluster entry in Rancher (Import Existing)

        Uses kubectl to create the provisioning.cattle.io/v1 Cluster CRD
        in Rancher's Kubernetes API.
        """
        logging(f"Creating Harvester management cluster entry: {cluster_name}")

        # Cluster CRD manifest
        cluster_manifest = {
            "apiVersion": "provisioning.cattle.io/v1",
            "kind": "Cluster",
            "metadata": {
                "name": cluster_name,
                "namespace": "fleet-default",
                "labels": {
                    "provider.cattle.io": "harvester"
                }
            },
            "spec": {}
        }

        # Write manifest to temp file
        fd, manifest_path = tempfile.mkstemp(suffix=".yaml", prefix="cluster-")
        with os.fdopen(fd, 'w') as f:
            yaml.dump(cluster_manifest, f)

        try:
            # Apply manifest using kubectl against Rancher
            rc, stdout, stderr = self._run_kubectl_rancher([
                "apply", "-f", manifest_path
            ])

            if rc != 0:
                raise Exception(f"Failed to create Harvester mgmt cluster: {stderr}")

            logging(f"Created Harvester management cluster: {cluster_name}")

            # Return the created cluster
            return self.get_harvester_mgmt_cluster(cluster_name)
        finally:
            # Cleanup temp file
            if os.path.exists(manifest_path):
                os.remove(manifest_path)

    def get_harvester_mgmt_cluster(self, cluster_name):
        """
        Get Harvester management cluster details using kubectl.

        Uses kubectl to get the provisioning.cattle.io/v1 Cluster CRD
        from Rancher's Kubernetes API.
        """
        logging(f"Getting Harvester management cluster: {cluster_name}", level="DEBUG")

        rc, stdout, stderr = self._run_kubectl_rancher([
            "get", "clusters.provisioning.cattle.io",
            cluster_name, "-n", "fleet-default",
            "-o", "json"
        ])

        if rc != 0:
            if "NotFound" in stderr or "not found" in stderr.lower():
                logging(f"Harvester mgmt cluster {cluster_name} not found")
                return None
            raise Exception(f"Failed to get Harvester mgmt cluster: {stderr}")

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse cluster response: {e}")

    def delete_harvester_mgmt_cluster(self, cluster_name):
        """
        Delete Harvester management cluster entry using kubectl.

        Uses kubectl to delete the provisioning.cattle.io/v1 Cluster CRD
        from Rancher's Kubernetes API.
        """
        logging(f"Deleting Harvester management cluster: {cluster_name}")

        rc, stdout, stderr = self._run_kubectl_rancher([
            "delete", "clusters.provisioning.cattle.io",
            cluster_name, "-n", "fleet-default",
            "--ignore-not-found"
        ])

        if rc != 0 and "NotFound" not in stderr and "not found" not in stderr.lower():
            raise Exception(f"Failed to delete Harvester mgmt cluster: {stderr}")

        logging(f"Deleted Harvester management cluster: {cluster_name}")

    def wait_for_harvester_ready(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """Wait for Harvester cluster to be ready in Rancher"""
        logging(f"Waiting for Harvester cluster {cluster_name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        iteration = 0
        while time.time() < end_time:
            try:
                cluster = self.get_harvester_mgmt_cluster(cluster_name)
                if cluster:
                    status = cluster.get("status", {})

                    # Check status.ready field (primary indicator)
                    if status.get("ready") is True:
                        logging(f"Harvester cluster {cluster_name} is ready (status.ready=true)")
                        return cluster

                    # Also check conditions for Ready type
                    conditions = status.get("conditions", [])
                    for condition in conditions:
                        if (condition.get("type") == "Ready" and
                                condition.get("status") == "True"):
                            logging(f"Harvester cluster {cluster_name} is ready (Ready condition)")
                            return cluster

                    # Log current state less frequently to avoid flooding
                    if iteration % 10 == 0:
                        ready_status = status.get("ready", "not set")
                        logging(
                            f"Cluster not ready yet. status.ready={ready_status}, "
                            f"conditions count={len(conditions)}"
                        )

            except Exception as e:
                if iteration % 10 == 0:
                    logging(f"Error checking cluster status: {e}", level="WARNING")

            iteration += 1
            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for Harvester cluster {cluster_name} to be ready")

    def wait_for_cluster_id(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for cluster to get its internal ID (status.clusterName).
        This appears shortly after cluster creation, before registration.
        """
        logging(f"Waiting for cluster {cluster_name} to get cluster ID")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                cluster = self.get_harvester_mgmt_cluster(cluster_name)
                if cluster:
                    cluster_id = cluster.get("status", {}).get("clusterName")
                    if cluster_id:
                        logging(f"Cluster {cluster_name} got ID: {cluster_id}")
                        return cluster
            except Exception as e:
                logging(f"Error checking cluster ID: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for cluster {cluster_name} to get cluster ID")

    def get_cluster_registration_url(self, cluster_id, rancher_endpoint, timeout=300):
        """
        Get cluster registration URL for importing Harvester using kubectl.

        Polls for the ClusterRegistrationToken CRD (management.cattle.io/v3)
        which is automatically created by Rancher after cluster creation.

        Args:
            cluster_id: The internal cluster ID (e.g., c-m-xxxxx)
            rancher_endpoint: Rancher server endpoint (used for logging)
            timeout: Maximum time to wait for token

        Returns:
            The manifest URL for cluster registration
        """
        logging(f"Getting cluster registration URL for cluster: {cluster_id}")

        # ClusterRegistrationTokens are management.cattle.io/v3 resources
        # They're named as {cluster_id}:default-token in the cluster's namespace
        token_name = "default-token"

        retry_count, retry_interval = get_retry_count_and_interval()
        end_time = time.time() + int(timeout)
        attempt = 0

        while time.time() < end_time:
            attempt += 1
            try:
                # Get ClusterRegistrationToken via kubectl
                rc, stdout, stderr = self._run_kubectl_rancher([
                    "get", "clusterregistrationtokens.management.cattle.io",
                    token_name, "-n", cluster_id,
                    "-o", "jsonpath={.status.manifestUrl}"
                ])

                # Log every 5 attempts to show progress
                if attempt % 5 == 1 or rc != 0:
                    stdout_preview = stdout[:100] if stdout else 'empty'
                    logging(f"Attempt {attempt}: rc={rc}, stdout={stdout_preview}")

                if rc == 0 and stdout:
                    manifest_url = stdout.strip()
                    if manifest_url:
                        logging(f"Got cluster registration URL: {manifest_url}")
                        return manifest_url
                    else:
                        if attempt % 5 == 1:
                            logging("manifestUrl not yet available, waiting...")
                elif "NotFound" in stderr or "not found" in stderr.lower():
                    if attempt % 5 == 1:
                        logging("Registration token not yet created, waiting...")
                else:
                    if attempt % 5 == 1:
                        logging(
                            f"Error getting registration token: {stderr}",
                            level="WARNING"
                        )
            except Exception as e:
                logging(
                    f"Error getting registration URL (attempt {attempt}): {e}",
                    level="WARNING"
                )

            time.sleep(retry_interval)

        raise Exception(
            f"Timeout waiting for cluster registration URL for {cluster_id} "
            f"after {attempt} attempts"
        )

    def set_cluster_registration_url(self, url):
        """Set cluster-registration-url setting in Harvester using kubectl.

        The value must be in JSON format matching Harvester structure:
        {'url': '...', 'insecureSkipTLSVerify': true/false}
        """
        logging(f"Setting cluster-registration-url to: {url}")

        # Format the value as JSON  object (matching Harvester's default structure)
        if url:
            value_obj = {"url": url, "insecureSkipTLSVerify": True}
            value = json.dumps(value_obj)
        else:
            value = '{"url":"","insecureSkipTLSVerify":false}'

        # Prepare patch data - the value itself is a JSON string
        patch_data = json.dumps({"value": value})

        # Use kubectl to patch the Harvester setting (runs against Harvester)
        cmd = ["kubectl", "patch", "settings.harvesterhci.io",
               "cluster-registration-url", "--type=merge", "-p", patch_data,
               "--insecure-skip-tls-verify"]

        logging(f"Running kubectl command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, input=None)  # nosec B603

        if result.returncode != 0:
            raise Exception(f"Failed to set cluster-registration-url: {result.stderr}")

        logging("Successfully set cluster-registration-url")

        logging("Successfully set cluster-registration-url")

    def get_all_rke2_versions(self, rancher_endpoint, max_versions=None):
        """
        Get all available RKE2 versions from Rancher.

        Args:
            rancher_endpoint: Rancher server endpoint
            max_versions: Maximum number of versions to return (None = all)

        Returns:
            List of version strings sorted by semantic version (newest first)
        """
        logging("Getting all RKE2 versions from Rancher")
        try:
            url = f"{rancher_endpoint}/v1-rke2-release/releases"
            response = requests.get(url, timeout=30, verify=False)  # nosec B501
            response.raise_for_status()

            data = response.json()
            versions = [r['id'] for r in data.get('data', [])]

            if not versions:
                raise Exception("No RKE2 versions available from Rancher")

            # Sort versions by semantic version (descending)
            from pkg_resources import parse_version
            sorted_versions = sorted(
                versions,
                key=lambda v: parse_version(v.split("+")[0].split("-")[0]),
                reverse=True
            )

            # Apply max_versions limit if specified
            if max_versions and max_versions > 0:
                sorted_versions = sorted_versions[:max_versions]

            logging(f"Found {len(sorted_versions)} RKE2 versions")
            return sorted_versions
        except Exception as e:
            raise Exception(f"Failed to get RKE2 versions: {e}")

    def get_rke2_version(self, target_version, rancher_endpoint):
        """
        Get RKE2 version from Rancher that matches target version.

        Args:
            target_version: Target version prefix (e.g. 'v1.28', 'v1.29')
            rancher_endpoint: Rancher server endpoint

        Returns:
            Full version string (e.g. 'v1.28.15+rke2r1')
        """
        logging(f"Getting RKE2 version for target: {target_version}")
        try:
            url = f"{rancher_endpoint}/v1-rke2-release/releases"
            response = requests.get(url, timeout=30, verify=False)  # nosec B501
            response.raise_for_status()

            data = response.json()
            versions = [r['id'] for r in data.get('data', [])]

            if not versions:
                raise Exception("No RKE2 versions available from Rancher")

            # Sort versions by semantic version (descending)
            from pkg_resources import parse_version
            sorted_versions = sorted(
                versions,
                key=lambda v: parse_version(v.split("+")[0].split("-")[0]),
                reverse=True
            )

            # Find first version matching target prefix
            for ver in sorted_versions:
                if ver.startswith(target_version):
                    logging(f"Selected RKE2 version: {ver}")
                    return ver

            raise Exception(
                f"No RKE2 version found matching '{target_version}'. "
                f"Available versions: {sorted_versions[:5]}"
            )
        except Exception as e:
            raise Exception(f"Failed to get RKE2 version: {e}")

    def create_cloud_credential(self, name, kubeconfig, cluster_id):
        """Create cloud credential for Harvester"""
        logging(f"Creating cloud credential: {name}")
        # Cloud credentials are managed by Rancher, use Rancher kubeconfig
        secret_spec = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": "cattle-global-data",
                "annotations": {
                    "provisioning.cattle.io/driver": "harvester"
                }
            },
            "type": "Opaque",
            "stringData": {
                "harvestercredentialConfig-clusterId": cluster_id,
                "harvestercredentialConfig-clusterType": "imported",
                "harvestercredentialConfig-kubeconfigContent": kubeconfig
            }
        }

        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(secret_spec)
        )
        if returncode != 0:
            raise Exception(f"Failed to create cloud credential: {stderr}")

        logging(f"Created cloud credential: {name}")
        return {"id": f"cattle-global-data:{name}", "metadata": {"name": name}}

    def get_cloud_credential(self, credential_id):
        """Get cloud credential details"""
        logging(f"Getting cloud credential: {credential_id}")
        parts = credential_id.split(":")
        namespace = parts[0] if len(parts) > 1 else "cattle-global-data"
        name = parts[-1]

        # Cloud credentials are in Rancher, use Rancher kubeconfig
        rc, stdout, stderr = self._run_kubectl_rancher([
            "get", "secret", name,
            "-n", namespace,
            "-o", "json"
        ])

        if rc == 0:
            import json
            return json.loads(stdout)
        elif "not found" in stderr.lower():
            return None
        else:
            raise Exception(f"Failed to get cloud credential: {stderr}")

    def delete_cloud_credential(self, credential_id):
        """Delete cloud credential"""
        logging(f"Deleting cloud credential: {credential_id}")
        parts = credential_id.split(":")
        namespace = parts[0] if len(parts) > 1 else "cattle-global-data"
        name = parts[-1]

        # Cloud credentials are in Rancher, use Rancher kubeconfig
        rc, stdout, stderr = self._run_kubectl_rancher([
            "delete", "secret", name,
            "-n", namespace,
            "--ignore-not-found=true"
        ])

        if rc == 0:
            logging(f"Deleted cloud credential: {credential_id}")
        else:
            raise Exception(f"Failed to delete cloud credential: {stderr}")

    def create_rke2_cluster(self, name, cloud_provider_config_id, hostname_prefix,
                            harvester_config_name, k8s_version, cloud_credential_id,
                            quantity, ingress="traefik"):
        """Create RKE2 cluster on Harvester"""
        logging(f"Creating RKE2 cluster: {name}")

        machine_global_config = {
            "cni": "calico",
            "disable-kube-proxy": False,
            "etcd-expose-metrics": False,
            "ingress-controller": ingress
        }

        drain_options = {
            "deleteEmptyDirData": True,
            "disableEviction": False,
            "enabled": False,
            "force": False,
            "gracePeriod": -1,
            "ignoreDaemonSets": True,
            "skipWaitForDeleteTimeoutSeconds": 0,
            "timeout": 120
        }

        cluster_spec = {
            "apiVersion": f"{self.rancher_provisioning_group}/{self.rancher_provisioning_version}",
            "kind": "Cluster",
            "metadata": {
                "name": name,
                "namespace": "fleet-default"
            },
            "spec": {
                "cloudCredentialSecretName": cloud_credential_id,
                "kubernetesVersion": k8s_version,
                "rkeConfig": {
                    "chartValues": {
                        "harvester-cloud-provider": {
                            "cloudConfigPath": (
                                "/var/lib/rancher/rke2/etc/config-files/"
                                "cloud-provider-config"
                            ),
                            "global": {
                                "cattle": {
                                    "clusterName": name
                                }
                            }
                        },
                        "rke2-calico": {},
                        "rke2-ingress-nginx": {},
                        "rke2-traefik": {}
                    },
                    "etcd": {
                        "snapshotRetention": 5,
                        "snapshotScheduleCron": "0 */5 * * *"
                    },
                    "machineGlobalConfig": machine_global_config,
                    "machinePools": [
                        {
                            "controlPlaneRole": True,
                            "etcdRole": True,
                            "workerRole": True,
                            "machineConfigRef": {
                                "kind": "HarvesterConfig",
                                "name": harvester_config_name
                            },
                            "name": "pool1",
                            "quantity": quantity,
                            "unhealthyNodeTimeout": "0s"
                        }
                    ],
                    "machineSelectorConfig": [
                        {
                            "config": {
                                "cloud-provider-config": f"secret://{cloud_provider_config_id}",
                                "cloud-provider-name": "harvester",
                                "protect-kernel-defaults": False
                            }
                        }
                    ],
                    "networking": {},
                    "registries": {},
                    "upgradeStrategy": {
                        "controlPlaneConcurrency": "1",
                        "controlPlaneDrainOptions": drain_options,
                        "workerConcurrency": "1",
                        "workerDrainOptions": drain_options
                    }
                }
            }
        }

        # RKE2 cluster is a Rancher resource, use Rancher kubeconfig
        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(cluster_spec)
        )
        if returncode != 0:
            raise Exception(f"Failed to create RKE2 cluster: {stderr}")

        logging(f"Created RKE2 cluster: {name}")
        return cluster_spec

    def get_rke2_cluster(self, cluster_name):
        """Get RKE2 cluster details"""
        return self.get_harvester_mgmt_cluster(cluster_name)

    def delete_rke2_cluster(self, cluster_name):
        """Delete RKE2 cluster"""
        return self.delete_harvester_mgmt_cluster(cluster_name)

    def wait_for_rke2_cluster_ready(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """Wait for RKE2 cluster to be fully ready.

        Waits until:
        - The controller has processed the latest spec
          (status.observedGeneration >= metadata.generation)
        - status.ready is True
        - Updated and Provisioned conditions are True
        - All machines in cluster.x-k8s.io are in Running phase
        """
        logging(f"Waiting for RKE2 cluster {cluster_name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        iteration = 0
        while time.time() < end_time:
            try:
                cluster = self.get_rke2_cluster(cluster_name)
                if cluster:
                    metadata = cluster.get("metadata", {})
                    status = cluster.get("status", {})
                    spec = cluster.get("spec", {})

                    # Ensure controller has processed the latest spec
                    generation = metadata.get("generation", 0)
                    observed = status.get("observedGeneration", 0)
                    if observed < generation:
                        if iteration % 10 == 0:
                            logging(f"Controller hasn't processed spec yet: "
                                    f"observed={observed}, generation={generation}")
                        iteration += 1
                        time.sleep(retry_interval)
                        continue

                    ready = status.get("ready") is True

                    # Check conditions
                    conditions = {c.get("type"): c.get("status")
                                  for c in status.get("conditions", [])}
                    updated = conditions.get("Updated") == "True"
                    provisioned = conditions.get("Provisioned") == "True"

                    # Count desired machines from spec
                    desired_pools = spec.get("rkeConfig", {}).get("machinePools", [])
                    total_desired = sum(int(p.get("quantity", 0)) for p in desired_pools)

                    # Count actual running machines via cluster.x-k8s.io
                    total_running = self._count_running_machines(cluster_name)

                    # For custom clusters (no machinePools), require at least 1
                    effective_desired = total_desired if total_desired > 0 else 1

                    if (ready and updated and provisioned
                            and total_running >= effective_desired):
                        logging(f"RKE2 cluster {cluster_name} is fully ready "
                                f"(machines: {total_running}/{total_desired})")
                        return cluster

                    if iteration % 10 == 0:
                        logging(f"RKE2 cluster not fully ready yet. "
                                f"ready={ready}, updated={updated}, "
                                f"provisioned={provisioned}, "
                                f"machines={total_running}/{total_desired}")

            except Exception as e:
                if iteration % 10 == 0:
                    logging(f"Error checking RKE2 cluster status: {e}", level="WARNING")

            iteration += 1
            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for RKE2 cluster {cluster_name} to be ready")

    def _count_running_machines(self, cluster_name):
        """Count machines in Running phase for a given cluster."""
        rc, stdout, stderr = self._run_kubectl_rancher([
            "get", "machines.cluster.x-k8s.io",
            "-n", "fleet-default",
            "-l", f"cluster.x-k8s.io/cluster-name={cluster_name}",
            "-o", "jsonpath={.items[*].status.phase}"
        ])
        if rc != 0 or not stdout.strip():
            return 0
        phases = stdout.strip().split()
        return sum(1 for p in phases if p == "Running")

    def wait_for_rke2_cluster_deleted(self, cluster_name, timeout=DEFAULT_TIMEOUT_LONG):
        """Wait for RKE2 cluster to be deleted"""
        logging(f"Waiting for RKE2 cluster {cluster_name} to be deleted")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            cluster = self.get_rke2_cluster(cluster_name)
            if cluster is None:
                logging(f"RKE2 cluster {cluster_name} has been deleted")
                return True
            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for RKE2 cluster {cluster_name} to be deleted")

    def scale_rke2_cluster(self, cluster_name, worker_count, harvester_config_name):
        """Scale RKE2 cluster by adding/removing a worker-only machine pool.

        If worker_count > 0, a 'worker-pool' is added (or updated).
        If worker_count == 0, the 'worker-pool' is removed.
        """
        logging(f"Scaling RKE2 cluster {cluster_name}: worker_count={worker_count}")

        # Get current cluster spec
        cluster = self.get_rke2_cluster(cluster_name)
        if not cluster:
            raise Exception(f"RKE2 cluster {cluster_name} not found")

        machine_pools = cluster.get("spec", {}).get("rkeConfig", {}).get("machinePools", [])

        # Remove existing worker-pool if present
        machine_pools = [p for p in machine_pools if p.get("name") != "worker-pool"]

        if int(worker_count) > 0:
            # Add worker-only pool
            worker_pool = {
                "controlPlaneRole": False,
                "etcdRole": False,
                "workerRole": True,
                "machineConfigRef": {
                    "kind": "HarvesterConfig",
                    "name": harvester_config_name
                },
                "name": "worker-pool",
                "quantity": int(worker_count),
                "unhealthyNodeTimeout": "0s"
            }
            machine_pools.append(worker_pool)

        # Patch the cluster using strategic merge patch to avoid annotation overflow
        patch = {
            "spec": {
                "rkeConfig": {
                    "machinePools": machine_pools
                }
            }
        }

        rc, stdout, stderr = self._run_kubectl_rancher(
            ["patch", "clusters.provisioning.cattle.io", cluster_name,
             "-n", "fleet-default", "--type=merge",
             "-p", json.dumps(patch)]
        )
        if rc != 0:
            raise Exception(f"Failed to scale RKE2 cluster: {stderr}")

        logging(f"Scaled RKE2 cluster {cluster_name} worker pool to {worker_count}")

    def upgrade_rke2_cluster(self, cluster_name, new_k8s_version):
        """Upgrade RKE2 cluster to a new Kubernetes version."""
        logging(f"Upgrading RKE2 cluster {cluster_name} to {new_k8s_version}")

        cluster = self.get_rke2_cluster(cluster_name)
        if not cluster:
            raise Exception(f"RKE2 cluster {cluster_name} not found")

        patch = {
            "spec": {
                "kubernetesVersion": new_k8s_version
            }
        }

        rc, stdout, stderr = self._run_kubectl_rancher(
            ["patch", "clusters.provisioning.cattle.io", cluster_name,
             "-n", "fleet-default", "--type=merge",
             "-p", json.dumps(patch)]
        )
        if rc != 0:
            raise Exception(f"Failed to upgrade RKE2 cluster: {stderr}")

        logging(f"Triggered upgrade of RKE2 cluster {cluster_name} to {new_k8s_version}")

    def create_harvester_config(self, name, cpus, mems, disks, image_id,
                                network_id, ssh_user, user_data):
        """Create Harvester config for RKE2 node template"""
        logging(f"Creating Harvester config: {name}")

        import base64

        # Build diskInfo and networkInfo as JSON structures
        disk_info = json.dumps({
            "disks": [{
                "imageName": image_id,
                "bootOrder": 1,
                "size": int(disks)
            }]
        })

        network_info = json.dumps({
            "interfaces": [{
                "networkName": network_id,
                "macAddress": ""
            }]
        })

        # Base64-encode userData as expected by the HarvesterConfig API
        encoded_user_data = ""
        if user_data:
            encoded_user_data = base64.b64encode(
                user_data.encode("utf-8")
            ).decode("utf-8")

        config_spec = {
            "apiVersion": (
                f"{self.rancher_machine_config_group}/"
                f"{self.rancher_machine_config_version}"
            ),
            "kind": "HarvesterConfig",
            "metadata": {
                "name": name,
                "namespace": "fleet-default"
            },
            "cpuCount": str(cpus),
            "memorySize": str(mems),
            "diskInfo": disk_info,
            "diskSize": "0",
            "imageName": "",
            "networkInfo": network_info,
            "networkName": "",
            "reservedMemorySize": "-1",
            "sshUser": ssh_user,
            "userData": encoded_user_data,
            "vmNamespace": DEFAULT_NAMESPACE
        }

        # HarvesterConfig is a Rancher resource, use Rancher kubeconfig
        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(config_spec)
        )
        if returncode != 0:
            raise Exception(f"Failed to create Harvester config: {stderr}")

        logging(f"Created Harvester config: {name}")
        return config_spec

    def generate_kubeconfig(self, cluster_id, cluster_name):
        """Generate full-access kubeconfig for Harvester cluster.

        Uses Rancher's generateKubeconfig action to get a kubeconfig with
        full access to the Harvester cluster. Used for cloud credentials.
        """
        logging(f"Generating kubeconfig for cluster: {cluster_name}")

        token = self._authenticate_rancher()

        url = (f"{self.rancher_endpoint.rstrip('/')}"
               f"/v3/clusters/{cluster_id}?action=generateKubeconfig")

        response = requests.post(
            url,
            json={},
            headers={"Authorization": f"Bearer {token}"},
            verify=False
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to generate kubeconfig: "
                f"{response.status_code}, {response.text}"
            )

        kubeconfig = response.json().get("config", "")
        logging("Generated kubeconfig for cluster")
        return kubeconfig

    def generate_cloud_provider_kubeconfig(self, cluster_id, cluster_name):
        """Generate cloud provider kubeconfig via Harvester kubeconfig API.

        Uses the Harvester-specific endpoint to generate a kubeconfig with
        the external Rancher URL and limited cloudprovider role. This is
        used for the cloud provider secret inside the guest VM.
        """
        logging(f"Generating cloud provider kubeconfig for cluster: {cluster_name}")

        token = self._authenticate_rancher()

        url = (f"{self.rancher_endpoint.rstrip('/')}"
               f"/k8s/clusters/{cluster_id}/v1/harvester/kubeconfig")
        data = {
            "clusterRoleName": "harvesterhci.io:cloudprovider",
            "namespace": "default",
            "serviceAccountName": cluster_name
        }

        response = requests.post(
            url,
            json=data,
            headers={"Authorization": f"Bearer {token}"},
            verify=False
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to generate harvester kubeconfig: "
                f"{response.status_code}, {response.text}"
            )

        kubeconfig = response.text.replace("\\n", "\n").strip('"')
        logging("Generated cloud provider kubeconfig for cluster")
        return kubeconfig

    def create_secret(self, name, data, annotations):
        """Create secret for cloud provider config"""
        logging(f"Creating secret: {name}")

        secret_spec = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": "fleet-default",
                "annotations": annotations
            },
            "type": "Opaque",
            "stringData": data
        }

        # Secret in fleet-default is a Rancher resource, use Rancher kubeconfig
        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(secret_spec)
        )
        if returncode != 0:
            raise Exception(f"Failed to create secret: {stderr}")

        logging(f"Created secret: {name}")
        return {"metadata": {"namespace": "fleet-default", "name": name}}

    def create_deployment(self, cluster_id, namespace, name, image, pvc=None,
                          command=None):
        """Create deployment in guest cluster"""
        logging(f"Creating deployment {name} in cluster {cluster_id}")

        container = {
            "name": name,
            "image": image,
        }
        if command:
            container["command"] = list(command)
        else:
            container["ports"] = [{"containerPort": 80}]

        deployment_spec = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "name": name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "name": name
                        }
                    },
                    "spec": {
                        "containers": [container]
                    }
                }
            }
        }

        if pvc:
            deployment_spec["spec"]["template"]["spec"]["volumes"] = [
                {"name": "data", "persistentVolumeClaim": {"claimName": pvc}}
            ]
            deployment_spec["spec"]["template"]["spec"]["containers"][0]["volumeMounts"] = [
                {"name": "data", "mountPath": "/data"}
            ]

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["apply", "-f", "-"],
            input_data=json.dumps(deployment_spec)
        )
        if rc != 0:
            raise Exception(f"Failed to create deployment: {stderr}")

        logging(f"Created deployment {name}")
        return deployment_spec

    def get_deployment(self, cluster_id, namespace, name):
        """Get deployment details from guest cluster via kubectl"""
        logging(f"Getting deployment {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["get", "deployment", name, "-n", namespace, "-o", "json"]
        )

        if rc != 0:
            if "NotFound" in stderr or "not found" in stderr.lower():
                return None
            raise Exception(f"Failed to get deployment: {stderr}")

        return json.loads(stdout)

    def delete_deployment(self, cluster_id, namespace, name):
        """Delete deployment from guest cluster via kubectl"""
        logging(f"Deleting deployment {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["delete", "deployment", name, "-n", namespace,
             "--ignore-not-found"]
        )

        if rc != 0:
            raise Exception(f"Failed to delete deployment: {stderr}")

        logging(f"Deleted deployment {name}")

    def wait_for_deployment_ready(self, cluster_id, namespace, name, timeout=DEFAULT_TIMEOUT):
        """Wait for deployment to be ready"""
        logging(f"Waiting for deployment {name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                deployment = self.get_deployment(cluster_id, namespace, name)
                if deployment:
                    status = deployment.get("status", {})
                    replicas = status.get("replicas", 0)
                    available = status.get("availableReplicas", 0)
                    if replicas > 0 and available >= replicas:
                        logging(f"Deployment {name} is ready")
                        return deployment
            except Exception as e:
                logging(f"Error checking deployment status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for deployment {name} to be ready")

    def wait_for_deployment_deleted(self, cluster_id, namespace, name, timeout=DEFAULT_TIMEOUT):
        """Wait for deployment to be deleted"""
        logging(f"Waiting for deployment {name} to be deleted")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            deployment = self.get_deployment(cluster_id, namespace, name)
            if deployment is None:
                logging(f"Deployment {name} has been deleted")
                return True
            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for deployment {name} to be deleted")

    def create_pvc(self, cluster_id, name, size="1Gi", storage_class=None):
        """Create PVC in guest cluster via kubectl"""
        logging(f"Creating PVC {name} in cluster {cluster_id}")

        pvc_spec = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": name,
                "namespace": DEFAULT_NAMESPACE
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {
                    "requests": {
                        "storage": size
                    }
                }
            }
        }
        if storage_class:
            pvc_spec["spec"]["storageClassName"] = storage_class

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["apply", "-f", "-"],
            input_data=json.dumps(pvc_spec)
        )
        if rc != 0:
            raise Exception(f"Failed to create PVC: {stderr}")

        logging(f"Created PVC {name}")
        return pvc_spec

    def get_pvc(self, cluster_id, name):
        """Get PVC details from guest cluster via kubectl"""
        logging(f"Getting PVC {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["get", "pvc", name, "-n", DEFAULT_NAMESPACE, "-o", "json"]
        )

        if rc != 0:
            if "NotFound" in stderr or "not found" in stderr.lower():
                return None
            raise Exception(f"Failed to get PVC: {stderr}")

        return json.loads(stdout)

    def delete_pvc(self, cluster_id, name):
        """Delete PVC from guest cluster via kubectl"""
        logging(f"Deleting PVC {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["delete", "pvc", name, "-n", DEFAULT_NAMESPACE,
             "--ignore-not-found"]
        )
        if rc != 0:
            raise Exception(f"Failed to delete PVC: {stderr}")

        logging(f"Deleted PVC {name}")

    def wait_for_pvc_bound(self, cluster_id, name, timeout=DEFAULT_TIMEOUT):
        """Wait for PVC to be bound"""
        logging(f"Waiting for PVC {name} to be bound")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                pvc = self.get_pvc(cluster_id, name)
                if pvc:
                    phase = pvc.get("status", {}).get("phase", "")
                    if phase == "Bound":
                        logging(f"PVC {name} is bound")
                        return pvc
            except Exception as e:
                logging(f"Error checking PVC status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for PVC {name} to be bound")

    def create_lb_service(self, cluster_id, service_data):
        """Create LoadBalancer service in guest cluster via kubectl"""
        name = service_data["metadata"]["name"]
        logging(f"Creating LoadBalancer service {name} in cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["apply", "-f", "-"],
            input_data=json.dumps(service_data)
        )
        if rc != 0:
            raise Exception(f"Failed to create LoadBalancer service: {stderr}")

        logging(f"Created LoadBalancer service {name}")
        return service_data

    def get_lb_service(self, cluster_id, name):
        """Get LoadBalancer service details from guest cluster via kubectl"""
        logging(f"Getting LoadBalancer service {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["get", "service", name, "-n", DEFAULT_NAMESPACE, "-o", "json"]
        )

        if rc != 0:
            if "NotFound" in stderr or "not found" in stderr.lower():
                return None
            raise Exception(f"Failed to get LoadBalancer service: {stderr}")

        return json.loads(stdout)

    def delete_lb_service(self, cluster_id, name):
        """Delete LoadBalancer service from guest cluster via kubectl"""
        logging(f"Deleting LoadBalancer service {name} from cluster {cluster_id}")

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["delete", "service", name, "-n", DEFAULT_NAMESPACE,
             "--ignore-not-found"]
        )
        if rc != 0:
            raise Exception(f"Failed to delete LoadBalancer service: {stderr}")

        logging(f"Deleted LoadBalancer service {name}")

    def wait_for_lb_service_ready(self, cluster_id, name, timeout=DEFAULT_TIMEOUT):
        """Wait for LoadBalancer service to be ready (IP assigned)"""
        logging(f"Waiting for LoadBalancer service {name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                service = self.get_lb_service(cluster_id, name)
                if service:
                    ingress = (service.get("status", {})
                               .get("loadBalancer", {})
                               .get("ingress", []))
                    if ingress and ingress[0].get("ip"):
                        ip = ingress[0]["ip"]
                        logging(f"LoadBalancer service {name} is ready with IP {ip}")
                        return service
            except Exception as e:
                logging(f"Error checking LoadBalancer status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for LoadBalancer service {name} to be ready")

    def query_lb_service(self, url, retries=10, interval=5):
        """Query LoadBalancer service endpoint with retries"""
        logging(f"Querying LoadBalancer service at: {url}")
        last_err = None
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=30, verify=False)  # nosec B501
                return response.status_code, response.text
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    logging(f"LB query attempt {attempt + 1}/{retries} failed: {e}, retrying...")
                    time.sleep(interval)
        raise Exception(
            f"Failed to query LoadBalancer service after {retries} attempts: {last_err}"
        )

    def query_lb_via_proxy(self, cluster_id, service_name, port=8080,
                           namespace="default", retries=10, interval=5):
        """Query LoadBalancer service via Rancher's k8s service proxy.

        Uses _run_kubectl_raw_guest to access the service proxy endpoint.
        """
        proxy_path = (f"/api/v1/namespaces/{namespace}/services/"
                      f"{service_name}:{port}/proxy/")
        logging(f"Querying LB via kubectl raw: {proxy_path}")
        last_err = None
        for attempt in range(retries):
            try:
                rc, stdout, stderr = self._run_kubectl_raw_guest(
                    cluster_id, proxy_path
                )
                if rc == 0:
                    return 200, stdout
                last_err = stderr
            except Exception as e:
                last_err = e
            if attempt < retries - 1:
                logging(f"LB proxy query attempt {attempt + 1}/{retries} "
                        f"failed: {last_err}, retrying...")
                time.sleep(interval)
        raise Exception(
            f"Failed to query LB via proxy after {retries} attempts: {last_err}"
        )

    def wait_for_harvester_deployments_ready(self, cluster_id, timeout=DEFAULT_TIMEOUT):
        """Wait for harvester-cloud-provider and harvester-csi-driver to be ready"""
        logging(f"Waiting for Harvester deployments in cluster {cluster_id}")
        deployments = ["harvester-cloud-provider", "harvester-csi-driver-controllers"]

        for deployment_name in deployments:
            self.wait_for_deployment_ready(cluster_id, "kube-system", deployment_name, timeout)

        logging("All Harvester deployments are ready")

    def create_cluster_network(self, name):
        """Create cluster network"""
        logging(f"Creating cluster network: {name}")

        spec = {
            "apiVersion": "network.harvesterhci.io/v1beta1",
            "kind": "ClusterNetwork",
            "metadata": {
                "name": name
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="clusternetworks",
                body=spec
            )
            logging(f"Created cluster network: {name}")
            return spec
        except ApiException as e:
            if e.status == 409:
                logging(f"Cluster network {name} already exists")
                return spec
            raise Exception(f"Failed to create cluster network: {e}")

    def delete_cluster_network(self, name):
        """Delete cluster network"""
        logging(f"Deleting cluster network: {name}")
        try:
            self.custom_api.delete_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="clusternetworks",
                name=name
            )
            logging(f"Deleted cluster network: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete cluster network: {e}")

    def create_vlan_config(self, name, cluster_network, nic):
        """Create VLAN config to bind NIC to cluster network"""
        logging(f"Creating VLAN config: {name} (nic={nic}, cluster_network={cluster_network})")

        spec = {
            "apiVersion": "network.harvesterhci.io/v1beta1",
            "kind": "VlanConfig",
            "metadata": {
                "name": name,
                "labels": {
                    "network.harvesterhci.io/clusternetwork": cluster_network
                }
            },
            "spec": {
                "clusterNetwork": cluster_network,
                "uplink": {
                    "bondOptions": {
                        "miimon": -1,
                        "mode": "active-backup"
                    },
                    "linkAttributes": {
                        "txQLen": -1
                    },
                    "nics": [nic]
                }
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="vlanconfigs",
                body=spec
            )
            logging(f"Created VLAN config: {name}")
            return spec
        except ApiException as e:
            if e.status == 409:
                logging(f"VLAN config {name} already exists")
                return spec
            raise Exception(f"Failed to create VLAN config: {e}")

    def delete_vlan_config(self, name):
        """Delete VLAN config"""
        logging(f"Deleting VLAN config: {name}")
        try:
            self.custom_api.delete_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="vlanconfigs",
                name=name
            )
            logging(f"Deleted VLAN config: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete VLAN config: {e}")

    def wait_for_cluster_network_ready(self, name, timeout=120):
        """Wait for cluster network to become ready"""
        logging(f"Waiting for cluster network {name} to be ready")
        deadline = time.time() + int(timeout)

        while time.time() < deadline:
            try:
                cn = self.custom_api.get_cluster_custom_object(
                    group="network.harvesterhci.io",
                    version="v1beta1",
                    plural="clusternetworks",
                    name=name
                )
                conditions = cn.get("status", {}).get("conditions", [])
                for cond in conditions:
                    if cond.get("type") == "ready" and cond.get("status") == "True":
                        logging(f"Cluster network {name} is ready")
                        return cn
            except ApiException:
                pass
            time.sleep(5)

        raise Exception(f"Cluster network {name} not ready within {timeout}s")

    def create_vlan_network(self, name, vlan_id, cluster_network):
        """Create VLAN network"""
        logging(f"Creating VLAN network: {name}")

        network_spec = {
            "apiVersion": "k8s.cni.cncf.io/v1",
            "kind": "NetworkAttachmentDefinition",
            "metadata": {
                "name": name,
                "namespace": DEFAULT_NAMESPACE,
                "annotations": {
                    "network.harvesterhci.io/route": '{"mode":"auto"}'
                },
                "labels": {
                    "network.harvesterhci.io/clusternetwork": cluster_network,
                    "network.harvesterhci.io/type": "L2VlanNetwork"
                }
            },
            "spec": {
                "config": json.dumps({
                    "cniVersion": "0.3.1",
                    "name": name,
                    "type": "bridge",
                    "bridge": f"{cluster_network}-br",
                    "promiscMode": True,
                    "vlan": int(vlan_id),
                    "ipam": {}
                })
            }
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="k8s.cni.cncf.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="network-attachment-definitions",
                body=network_spec
            )
            logging(f"Created VLAN network: {name}")
            return network_spec
        except ApiException as e:
            if e.status == 409:  # Already exists
                logging(f"VLAN network {name} already exists")
                return network_spec
            raise Exception(f"Failed to create VLAN network: {e}")

    def delete_vlan_network(self, name):
        """Delete VLAN network"""
        logging(f"Deleting VLAN network: {name}")
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="k8s.cni.cncf.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="network-attachment-definitions",
                name=name
            )
            logging(f"Deleted VLAN network: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete VLAN network: {e}")

    def get_ip_pool(self, name):
        """Get IP pool by name, returns None if not found"""
        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"
        try:
            return self.custom_api.get_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get IP pool: {e}")

    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """Create IP pool, reusing existing pool with the same name"""
        logging(f"Creating IP pool: {name}")

        existing = self.get_ip_pool(name)
        if existing:
            logging(f"IP pool {name} already exists, reusing")
            return existing

        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"

        ippool_spec = {
            "apiVersion": f"{lb_group}/{lb_version}",
            "kind": "IPPool",
            "metadata": {
                "name": name
            },
            "spec": {
                "ranges": [{
                    "subnet": subnet,
                    "rangeStart": start_ip,
                    "rangeEnd": end_ip,
                    "gateway": "",
                    "type": "range" if start_ip or end_ip else "cidr"
                }],
                "selector": {
                    "network": network_id,
                    "scope": [{
                        "namespace": "*",
                        "project": "*",
                        "guestCluster": "*"
                    }]
                }
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                body=ippool_spec
            )
            logging(f"Created IP pool: {name}")
            return ippool_spec
        except ApiException as e:
            if e.status == 409:  # Already exists
                logging(f"IP pool {name} already exists")
                return ippool_spec
            raise Exception(f"Failed to create IP pool: {e}")

    def delete_ip_pool(self, name):
        """Delete IP pool"""
        logging(f"Deleting IP pool: {name}")

        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"

        try:
            self.custom_api.delete_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                name=name
            )
            logging(f"Deleted IP pool: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete IP pool: {e}")

    def create_image(self, name, url):
        """Create image by URL"""
        logging(f"Creating image: {name}")

        image_spec = {
            "apiVersion": f"{self.harvester_group}/{self.harvester_version}",
            "kind": "VirtualMachineImage",
            "metadata": {
                "name": name,
                "namespace": DEFAULT_NAMESPACE
            },
            "spec": {
                "displayName": name,
                "sourceType": "download",
                "url": url
            }
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group=self.harvester_group,
                version=self.harvester_version,
                namespace=DEFAULT_NAMESPACE,
                plural="virtualmachineimages",
                body=image_spec
            )
            logging(f"Created image: {name}")
            return image_spec
        except ApiException as e:
            raise Exception(f"Failed to create image: {e}")

    def wait_for_image_ready(self, name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be ready"""
        logging(f"Waiting for image {name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        last_logged_progress = -1
        check_count = 0
        while time.time() < end_time:
            try:
                image = self.custom_api.get_namespaced_custom_object(
                    group=self.harvester_group,
                    version=self.harvester_version,
                    namespace=DEFAULT_NAMESPACE,
                    plural="virtualmachineimages",
                    name=name
                )
                progress = image.get("status", {}).get("progress", 0)
                check_count += 1

                if progress == 100:
                    logging(f"Image {name} is ready")
                    return image

                # Only log if progress changed by 5% or more, or every 10th check
                if (abs(progress - last_logged_progress) >= 5 or check_count % 10 == 1):
                    logging(f"Image {name} progress: {progress}%", level="DEBUG")
                    last_logged_progress = progress
            except Exception as e:
                logging(f"Error checking image status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for image {name} to be ready")

    def delete_image(self, name):
        """Delete image"""
        logging(f"Deleting image: {name}")
        try:
            self.custom_api.delete_namespaced_custom_object(
                group=self.harvester_group,
                version=self.harvester_version,
                namespace=DEFAULT_NAMESPACE,
                plural="virtualmachineimages",
                name=name
            )
            logging(f"Deleted image: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete image: {e}")

    # Import Existing Cluster Operations
    def create_import_cluster(self, name):
        """Create a minimal provisioning cluster for import."""
        logging(f"Creating import cluster: {name}")

        cluster_spec = {
            "apiVersion": (
                f"{self.rancher_provisioning_group}"
                f"/{self.rancher_provisioning_version}"
            ),
            "kind": "Cluster",
            "metadata": {
                "name": name,
                "namespace": "fleet-default"
            },
            "spec": {}
        }

        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(cluster_spec)
        )
        if returncode != 0:
            raise Exception(
                f"Failed to create import cluster: {stderr}"
            )

        logging(f"Created import cluster: {name}")
        return cluster_spec

    def wait_for_import_cluster_ready(self, cluster_name,
                                      timeout=DEFAULT_TIMEOUT_LONG):
        """Wait for an imported cluster to become active in Rancher.

        Does NOT check machinePools or cluster.x-k8s.io machines.
        """
        logging(f"Waiting for import cluster {cluster_name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        iteration = 0
        while time.time() < end_time:
            try:
                cluster = self.get_rke2_cluster(cluster_name)
                if cluster:
                    metadata = cluster.get("metadata", {})
                    status = cluster.get("status", {})

                    generation = metadata.get("generation", 0)
                    observed = status.get("observedGeneration", 0)
                    if observed < generation:
                        if iteration % 10 == 0:
                            logging(
                                f"Controller hasn't processed spec yet: "
                                f"observed={observed}, "
                                f"generation={generation}"
                            )
                        iteration += 1
                        time.sleep(retry_interval)
                        continue

                    ready = status.get("ready") is True

                    conditions = {
                        c.get("type"): c.get("status")
                        for c in status.get("conditions", [])
                    }
                    connected = conditions.get("Connected") == "True"
                    ready_cond = conditions.get("Ready") == "True"

                    if ready and (connected or ready_cond):
                        logging(
                            f"Import cluster {cluster_name} is ready"
                        )
                        return cluster

                    if iteration % 10 == 0:
                        logging(
                            f"Import cluster not ready yet. "
                            f"ready={ready}, connected={connected}, "
                            f"ready_cond={ready_cond}"
                        )

            except Exception as e:
                if iteration % 10 == 0:
                    logging(
                        f"Error checking import cluster status: {e}",
                        level="WARNING"
                    )

            iteration += 1
            time.sleep(retry_interval)

        raise Exception(
            f"Timeout waiting for import cluster {cluster_name} to be ready"
        )

    # Custom RKE2 Cluster Operations
    def create_custom_rke2_cluster(self, name, cloud_provider_config_id,
                                   k8s_version, cloud_credential_id,
                                   ingress="traefik"):
        """Create a custom RKE2 cluster without machinePools."""
        logging(f"Creating custom RKE2 cluster: {name}")

        machine_global_config = {
            "cni": "calico",
            "disable-kube-proxy": False,
            "etcd-expose-metrics": False,
            "ingress-controller": ingress
        }

        drain_options = {
            "deleteEmptyDirData": True,
            "disableEviction": False,
            "enabled": False,
            "force": False,
            "gracePeriod": -1,
            "ignoreDaemonSets": True,
            "skipWaitForDeleteTimeoutSeconds": 0,
            "timeout": 120
        }

        cluster_spec = {
            "apiVersion": (
                f"{self.rancher_provisioning_group}"
                f"/{self.rancher_provisioning_version}"
            ),
            "kind": "Cluster",
            "metadata": {
                "name": name,
                "namespace": "fleet-default"
            },
            "spec": {
                "cloudCredentialSecretName": cloud_credential_id,
                "kubernetesVersion": k8s_version,
                "rkeConfig": {
                    "chartValues": {
                        "harvester-cloud-provider": {
                            "cloudConfigPath": (
                                "/var/lib/rancher/rke2/etc/config-files/"
                                "cloud-provider-config"
                            ),
                            "global": {
                                "cattle": {
                                    "clusterName": name
                                }
                            }
                        },
                        "rke2-calico": {},
                        "rke2-ingress-nginx": {},
                        "rke2-traefik": {}
                    },
                    "etcd": {
                        "snapshotRetention": 5,
                        "snapshotScheduleCron": "0 */5 * * *"
                    },
                    "machineGlobalConfig": machine_global_config,
                    "machineSelectorConfig": [
                        {
                            "config": {
                                "cloud-provider-config": (
                                    f"secret://{cloud_provider_config_id}"
                                ),
                                "cloud-provider-name": "harvester",
                                "protect-kernel-defaults": False
                            }
                        }
                    ],
                    "networking": {},
                    "registries": {},
                    "upgradeStrategy": {
                        "controlPlaneConcurrency": "1",
                        "controlPlaneDrainOptions": drain_options,
                        "workerConcurrency": "1",
                        "workerDrainOptions": drain_options
                    }
                }
            }
        }

        returncode, stdout, stderr = self._run_kubectl_rancher(
            ["apply", "-f", "-"],
            input_data=json.dumps(cluster_spec)
        )
        if returncode != 0:
            raise Exception(
                f"Failed to create custom RKE2 cluster: {stderr}"
            )

        logging(f"Created custom RKE2 cluster: {name}")
        return cluster_spec

    def update_cluster_chart_name(self, cluster_name, mgmt_cluster_id):
        """Patch the custom cluster's chartValues with the real management ID."""
        logging(f"Updating clusterName to {mgmt_cluster_id} for {cluster_name}")

        patch = {
            "spec": {
                "rkeConfig": {
                    "chartValues": {
                        "harvester-cloud-provider": {
                            "global": {
                                "cattle": {
                                    "clusterName": mgmt_cluster_id
                                }
                            }
                        }
                    }
                }
            }
        }

        rc, stdout, stderr = self._run_kubectl_rancher(
            ["patch", "clusters.provisioning.cattle.io", cluster_name,
             "-n", "fleet-default", "--type=merge",
             "-p", json.dumps(patch)]
        )

        if rc != 0:
            raise Exception(
                f"Failed to update clusterName for {cluster_name}: "
                f"{stderr[:500]}"
            )

        logging(f"Updated clusterName to {mgmt_cluster_id}")

    def fix_cloud_provider_cluster_name(self, cluster_id):
        """Fix the cloud-provider --cluster-name arg on the guest cluster.

        Rancher's provisioning controller deploys the cloud-provider chart
        with the provisioning name instead of the management cluster ID.
        The cloud provider uses --cluster-name to match VMs via the
        harvesterhci.io/owned-by label, which Rancher sets to the mgmt ID.

        This waits for the deployment to exist, patches the arg, then waits
        for the rolling update to complete.

        Args:
            cluster_id: Management cluster ID (e.g. c-m-xxxxx)
        """
        logging(f"Fixing cloud provider clusterName to {cluster_id}")

        # Wait for the cloud-provider deployment to exist
        deploy = self.wait_for_deployment_ready(
            cluster_id, "kube-system", "harvester-cloud-provider"
        )

        containers = deploy["spec"]["template"]["spec"]["containers"]

        for idx, container in enumerate(containers):
            if "cloud-provider" not in container.get("name", ""):
                continue

            args = container.get("args", [])
            json_patch = None

            for arg_idx, arg in enumerate(args):
                if arg.startswith("--cluster-name"):
                    current = arg.split("=", 1)[1] if "=" in arg else ""
                    if current == cluster_id:
                        logging(f"clusterName already correct: {cluster_id}")
                        return
                    json_patch = [{
                        "op": "replace",
                        "path": (
                            f"/spec/template/spec/containers/{idx}"
                            f"/args/{arg_idx}"
                        ),
                        "value": f"--cluster-name={cluster_id}"
                    }]
                    break

            if json_patch is None:
                # --cluster-name not present, add it
                json_patch = [{
                    "op": "add",
                    "path": (
                        f"/spec/template/spec/containers/{idx}/args/-"
                    ),
                    "value": f"--cluster-name={cluster_id}"
                }]

            rc, stdout, stderr = self._run_kubectl_guest(
                cluster_id,
                ["patch", "deployment", "harvester-cloud-provider",
                 "-n", "kube-system", "--type=json",
                 "-p", json.dumps(json_patch)]
            )

            if rc != 0:
                raise Exception(
                    f"Failed to patch cloud-provider: {stderr[:300]}"
                )

            logging(f"Patched --cluster-name to {cluster_id}, "
                    f"waiting for rollout")

            # Wait for the rolling update to complete
            rc, stdout, stderr = self._run_kubectl_guest(
                cluster_id,
                ["rollout", "status",
                 "deployment/harvester-cloud-provider",
                 "-n", "kube-system", "--timeout=300s"]
            )
            if rc != 0:
                logging(f"Rollout warning: {stderr[:200]}",
                        level="WARNING")

            logging("Cloud provider deployment rolled out with "
                    "correct clusterName")
            return

        raise Exception(
            "Could not find cloud-provider container in deployment"
        )

    def get_cluster_registration_command(self, cluster_name,
                                         timeout=DEFAULT_TIMEOUT_LONG):
        """Get the insecure node registration command for a custom cluster."""
        logging(f"Getting registration command for cluster: {cluster_name}")

        # Get the management cluster ID
        cluster = self.get_rke2_cluster(cluster_name)
        if not cluster:
            raise Exception(f"Cluster {cluster_name} not found")

        cluster_id = cluster.get("status", {}).get("clusterName", "")
        if not cluster_id:
            raise Exception(
                f"Cluster {cluster_name} has no management cluster ID yet"
            )

        logging(f"Management cluster ID: {cluster_id}")
        token_name = "default-token"

        retry_count, retry_interval = get_retry_count_and_interval()
        end_time = time.time() + int(timeout)
        attempt = 0

        while time.time() < end_time:
            attempt += 1
            try:
                rc, stdout, stderr = self._run_kubectl_rancher([
                    "get",
                    "clusterregistrationtokens.management.cattle.io",
                    token_name, "-n", cluster_id,
                    "-o", "jsonpath={.status.insecureNodeCommand}"
                ])

                if attempt % 5 == 1 or rc != 0:
                    logging(f"Attempt {attempt}: rc={rc}")

                if rc == 0 and stdout and stdout.strip():
                    logging("Got cluster registration command")
                    return stdout.strip()
                elif "NotFound" in stderr or "not found" in stderr.lower():
                    if attempt % 5 == 1:
                        logging(
                            "Registration token not yet created, waiting..."
                        )
                else:
                    if attempt % 5 == 1:
                        logging(
                            "insecureNodeCommand not yet available, "
                            "waiting...",
                            level="DEBUG"
                        )
            except Exception as e:
                logging(
                    f"Error getting registration command "
                    f"(attempt {attempt}): {e}",
                    level="WARNING"
                )

            time.sleep(retry_interval)

        raise Exception(
            f"Timeout waiting for registration command for {cluster_name} "
            f"after {attempt} attempts"
        )

    # Harvester VM Operations (for custom cluster nodes)
    def create_harvester_vm(self, name, image_id, network_id, cpus, memory,
                            disk_size, ssh_user, user_data, network_data="",
                            guest_cluster_id=""):
        """Create a VM on Harvester using the Kubernetes custom API.

        Builds the VirtualMachine manifest directly (same pattern as vm/crd.py)
        to avoid any dependency on the harvester_api package, which is shadowed
        by libs/harvester_api.py when Robot Framework prepends libs/ to sys.path.
        """
        logging(f"Creating Harvester VM: {name}")

        disk_name = f"{name}-disk-0"
        disk_size_gi = f"{disk_size}Gi"

        # Look up the image's actual storage class from Harvester.
        # Harvester dynamically creates a storage class (lh-<uuid>) per image;
        # the name cannot be guessed — it must be read from the image status.
        image_ns, image_name = (
            image_id.split("/", 1) if "/" in image_id
            else (DEFAULT_NAMESPACE, image_id)
        )
        try:
            img_obj = self.custom_api.get_namespaced_custom_object(
                group="harvesterhci.io",
                version="v1beta1",
                namespace=image_ns,
                plural="virtualmachineimages",
                name=image_name
            )
            storage_class = img_obj.get("status", {}).get("storageClassName", "")
            if not storage_class:
                raise Exception(
                    f"Image {image_id} has no storageClassName in status"
                )
            logging(f"Resolved storage class for image {image_id}: {storage_class}")
        except ApiException as e:
            raise Exception(
                f"Failed to look up image {image_id} for storage class: {e}"
            )

        volume_claim_templates = [
            {
                "metadata": {
                    "name": disk_name,
                    "annotations": {
                        "harvesterhci.io/imageId": image_id
                    }
                },
                "spec": {
                    "accessModes": ["ReadWriteMany"],
                    "resources": {"requests": {"storage": disk_size_gi}},
                    "volumeMode": "Block",
                    "storageClassName": storage_class
                }
            }
        ]

        # Build network interfaces: when a VLAN network is provided, use only
        # the bridge interface on the VLAN (matching Harvester UI behaviour).
        # This gives the VM a routable VLAN IP as its primary address.
        # Fall back to masquerade/pod network when no VLAN is specified.
        if network_id:
            interfaces = [
                {"bridge": {}, "model": "virtio", "name": "default"}
            ]
            networks = [
                {"name": "default", "multus": {"networkName": network_id}}
            ]
        else:
            interfaces = [
                {"masquerade": {}, "model": "virtio", "name": "default"}
            ]
            networks = [{"name": "default", "pod": {}}]

        # Volumes: root disk + cloud-init
        volumes = [
            {"name": "rootdisk", "persistentVolumeClaim": {"claimName": disk_name}},
            {
                "name": "cloudinitdisk",
                "cloudInitNoCloud": {
                    "userData": user_data or "#cloud-config\n",
                    **({
                        "networkData": network_data
                    } if network_data else {})
                }
            }
        ]

        disks = [
            {"name": "rootdisk", "disk": {"bus": "virtio"}, "bootOrder": 1},
            {"name": "cloudinitdisk", "disk": {"bus": "virtio"}}
        ]

        memory_gi = f"{memory}Gi" if str(memory).isdigit() else str(memory)

        # VM-level labels
        vm_labels = {
            "harvesterhci.io/creator": "robot-framework",
            "harvesterhci.io/os": "linux"
        }
        # Pod template labels
        pod_labels = {"harvesterhci.io/vmName": name}

        # When a guest cluster ID is provided, add the labels the
        # Harvester LB webhook requires to discover guest-cluster VMs.
        if guest_cluster_id:
            vm_labels["harvesterhci.io/creator"] = (
                "docker-machine-driver-harvester"
            )
            vm_labels["guestcluster.harvesterhci.io/name"] = (
                guest_cluster_id
            )
            pod_labels["harvesterhci.io/creator"] = (
                "docker-machine-driver-harvester"
            )
            pod_labels["guestcluster.harvesterhci.io/name"] = (
                guest_cluster_id
            )

        vm_dict = {
            "apiVersion": "kubevirt.io/v1",
            "kind": "VirtualMachine",
            "metadata": {
                "name": name,
                "namespace": DEFAULT_NAMESPACE,
                "annotations": {
                    "harvesterhci.io/vmRunStrategy": "RerunOnFailure",
                    "harvesterhci.io/volumeClaimTemplates": (
                        json.dumps(volume_claim_templates)
                    ),
                    "harvesterhci.io/sshNames": "[]"
                },
                "labels": vm_labels
            },
            "spec": {
                "runStrategy": "RerunOnFailure",
                "template": {
                    "metadata": {
                        "annotations": {"harvesterhci.io/sshNames": "[]"},
                        "labels": pod_labels
                    },
                    "spec": {
                        "affinity": {},
                        "architecture": "amd64",
                        "domain": {
                            "cpu": {
                                "cores": int(cpus),
                                "sockets": 1,
                                "threads": 1
                            },
                            "devices": {
                                "inputs": [
                                    {"bus": "usb", "name": "tablet",
                                     "type": "tablet"}
                                ],
                                "interfaces": interfaces,
                                "disks": disks
                            },
                            "features": {"acpi": {"enabled": True}},
                            "machine": {"type": "q35"},
                            "memory": {"guest": memory_gi},
                            "resources": {
                                "limits": {
                                    "cpu": str(cpus),
                                    "memory": memory_gi
                                },
                                "requests": {
                                    "cpu": "125m",
                                    "memory": "2730Mi"
                                }
                            }
                        },
                        "evictionStrategy": "LiveMigrateIfPossible",
                        "hostname": name,
                        "networks": networks,
                        "terminationGracePeriodSeconds": 120,
                        "volumes": volumes
                    }
                }
            }
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="kubevirt.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="virtualmachines",
                body=vm_dict
            )
            logging(f"Created Harvester VM: {name}")
            return vm_dict
        except ApiException as e:
            raise Exception(f"Failed to create VM {name}: {e}")

    def wait_for_harvester_vm_ready(self, name, timeout=DEFAULT_TIMEOUT):
        """Wait for a Harvester VM to be running."""
        logging(f"Waiting for VM {name} to be running")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                vmi = self.custom_api.get_namespaced_custom_object(
                    group="kubevirt.io",
                    version="v1",
                    namespace=DEFAULT_NAMESPACE,
                    plural="virtualmachineinstances",
                    name=name
                )
                phase = vmi.get("status", {}).get("phase", "")
                if phase == "Running":
                    logging(f"VM {name} is running")
                    return vmi
                logging(f"VM {name} phase: {phase}", level="DEBUG")
            except ApiException as e:
                if e.status != 404:
                    logging(
                        f"Error checking VM status: {e}", level="WARNING"
                    )

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for VM {name} to be running")

    def delete_harvester_vm(self, name):
        """Delete a Harvester VM and its associated volume."""
        logging(f"Deleting Harvester VM: {name}")
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="kubevirt.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="virtualmachines",
                name=name
            )
            logging(f"Deleted Harvester VM: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(f"Failed to delete VM {name}: {e}")

        # Delete the volume (PVC) created by volumeClaimTemplates
        disk_pvc = f"{name}-disk-0"
        logging(f"Deleting VM volume: {disk_pvc}")
        try:
            self.core_api.delete_namespaced_persistent_volume_claim(
                name=disk_pvc,
                namespace=DEFAULT_NAMESPACE
            )
            logging(f"Deleted VM volume: {disk_pvc}")
        except ApiException as e:
            if e.status != 404:
                logging(f"Failed to delete volume {disk_pvc}: {e}",
                        level="WARNING")

    # Chart Install Operations (for import clusters)
    def install_chart(self, cluster_id, repo_name, chart_name, version,
                      release_name, namespace, values=None):
        """Install a Helm chart on a guest cluster via Rancher catalog API.

        Uses _run_kubectl_raw_guest to POST to the Steve catalog install
        action on the correct guest cluster.

        Args:
            cluster_id: Rancher management cluster ID (e.g. c-m-xxxxx)
            repo_name: Chart repository name (e.g. rancher-charts)
            chart_name: Chart name (e.g. harvester-cloud-provider)
            version: Chart version
            release_name: Helm release name
            namespace: Target namespace for the chart
            values: Optional dict of chart values overrides
        """
        logging(f"Installing chart {chart_name} v{version} as {release_name} "
                f"in {namespace} on cluster {cluster_id}")

        payload = {
            "charts": [
                {
                    "chartName": chart_name,
                    "version": version,
                    "releaseName": release_name,
                    "annotations": {
                        "catalog.cattle.io/ui-source-repo": repo_name,
                        "catalog.cattle.io/ui-source-repo-type": "cluster"
                    },
                    "values": values or {}
                }
            ],
            "namespace": namespace
        }

        rc, stdout, stderr = self._run_kubectl_raw_guest(
            cluster_id,
            f"/v1/catalog.cattle.io.clusterrepos/{repo_name}"
            f"?action=install",
            method="create",
            input_data=json.dumps(payload)
        )

        if rc != 0:
            raise Exception(
                f"Failed to install chart {chart_name}: {stderr[:500]}"
            )

        logging(f"Chart install initiated: {chart_name} v{version}")
        return json.loads(stdout) if stdout.strip() else {}

    def create_cluster_repo(self, cluster_id, repo_name, git_url, git_branch):
        """Create a ClusterRepo on a guest cluster via kubectl.

        Args:
            cluster_id: Rancher management cluster ID
            repo_name: Name for the ClusterRepo resource
            git_url: Git repository URL
            git_branch: Git branch name
        """
        logging(f"Creating ClusterRepo {repo_name} on cluster {cluster_id} "
                f"(branch={git_branch})")

        repo_spec = {
            "apiVersion": "catalog.cattle.io/v1",
            "kind": "ClusterRepo",
            "metadata": {
                "name": repo_name
            },
            "spec": {
                "gitRepo": git_url,
                "gitBranch": git_branch
            }
        }

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["apply", "-f", "-"],
            input_data=json.dumps(repo_spec)
        )

        if rc != 0:
            if "AlreadyExists" in stderr:
                logging(f"ClusterRepo {repo_name} already exists")
                return repo_spec
            raise Exception(
                f"Failed to create ClusterRepo {repo_name}: {stderr[:500]}"
            )

        logging(f"Created ClusterRepo {repo_name}")
        return repo_spec

    def wait_for_cluster_repo_ready(self, cluster_id, repo_name,
                                    timeout=DEFAULT_TIMEOUT):
        """Wait for a ClusterRepo to finish downloading on a guest cluster.

        Requires Downloaded=True on two consecutive polls to avoid the
        false-positive that occurs briefly after initial creation before
        the controller begins the real download.

        Args:
            cluster_id: Rancher management cluster ID
            repo_name: ClusterRepo name
            timeout: Maximum wait time in seconds
        """
        logging(f"Waiting for ClusterRepo {repo_name} to be ready")
        end_time = time.time() + int(timeout)
        consecutive_ready = 0

        while time.time() < end_time:
            rc, stdout, stderr = self._run_kubectl_guest(
                cluster_id,
                ["get", "clusterrepos.catalog.cattle.io", repo_name,
                 "-o", "json"]
            )
            downloaded = False
            if rc == 0 and stdout.strip():
                data = json.loads(stdout)
                conditions = data.get("status", {}).get("conditions", [])
                for c in conditions:
                    if (c.get("type") == "Downloaded" and
                            c.get("status") == "True"):
                        downloaded = True
                        break

            if downloaded:
                consecutive_ready += 1
                if consecutive_ready >= 2:
                    logging(f"ClusterRepo {repo_name} is ready "
                            f"(stable after {consecutive_ready} checks)")
                    return data
            else:
                consecutive_ready = 0

            time.sleep(5)

        raise Exception(
            f"ClusterRepo {repo_name} not ready after {timeout}s"
        )

    def get_chart_versions(self, repo_name, chart_name, cluster_id=None):
        """Get available versions for a chart from a Rancher chart repo.

        When cluster_id is given, retries up to 60s for the chart index
        to be populated (it can lag behind the Downloaded condition).

        Args:
            repo_name: Chart repository name
            chart_name: Chart name
            cluster_id: Optional guest cluster ID; when provided, queries
                        the guest cluster repo via kubectl

        Returns:
            list: Available version strings, newest first
        """
        logging(f"Getting versions for chart {chart_name} from {repo_name}")

        max_attempts = 12 if cluster_id else 1
        for attempt in range(max_attempts):
            if cluster_id:
                rc, stdout, stderr = self._run_kubectl_raw_guest(
                    cluster_id,
                    f"/v1/catalog.cattle.io.clusterrepos/{repo_name}"
                    f"?link=index"
                )
            else:
                rc, stdout, stderr = self._run_kubectl_rancher(
                    ["get", "--raw",
                     f"/v1/catalog.cattle.io.clusterrepos/{repo_name}"
                     f"?link=index"]
                )

            if rc != 0:
                if attempt < max_attempts - 1:
                    logging(f"Chart index not available yet, retrying "
                            f"({attempt + 1}/{max_attempts})...")
                    time.sleep(5)
                    continue
                raise Exception(
                    f"Failed to get chart index: {stderr}"
                )

            data = json.loads(stdout)
            entries = data.get("entries", {})
            chart_entries = entries.get(chart_name, [])
            versions = [e.get("version", "") for e in chart_entries]

            if versions or attempt >= max_attempts - 1:
                logging(f"Found {len(versions)} versions for {chart_name}: "
                        f"{versions[:5]}")
                return versions

            logging(f"Chart {chart_name} not in index yet, retrying "
                    f"({attempt + 1}/{max_attempts})...")
            time.sleep(5)

        return []

    def create_cloud_config_secret(self, cluster_id, secret_name,
                                   namespace, kubeconfig):
        """Create a cloud-provider-config secret on a guest cluster.

        Args:
            cluster_id: Rancher management cluster ID
            secret_name: Name for the secret
            namespace: Target namespace (typically kube-system)
            kubeconfig: The Harvester cloud-provider kubeconfig content

        Returns:
            dict: Created secret spec
        """
        logging(f"Creating cloud config secret {secret_name} in "
                f"{namespace} on cluster {cluster_id}")

        import base64
        encoded = base64.b64encode(
            kubeconfig.encode("utf-8")
        ).decode("utf-8")

        secret_spec = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": secret_name,
                "namespace": namespace
            },
            "type": "Opaque",
            "data": {
                "cloud-provider-config": encoded
            }
        }

        rc, stdout, stderr = self._run_kubectl_guest(
            cluster_id,
            ["apply", "-f", "-"],
            input_data=json.dumps(secret_spec)
        )

        if rc != 0:
            if "AlreadyExists" in stderr:
                logging(f"Secret {secret_name} already exists")
                return secret_spec
            raise Exception(
                f"Failed to create cloud config secret: {stderr[:300]}"
            )

        logging(f"Created cloud config secret: {secret_name}")
        return secret_spec

    def wait_for_chart_app_ready(self, cluster_id, release_name,
                                 namespace, timeout=DEFAULT_TIMEOUT):
        """Wait for a chart app to be deployed and ready.

        Args:
            cluster_id: Rancher management cluster ID
            release_name: Helm release name
            namespace: Namespace where the chart was installed
            timeout: Timeout in seconds
        """
        logging(f"Waiting for chart app {release_name} to be ready "
                f"in {namespace}")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        iteration = 0
        while time.time() < end_time:
            try:
                rc, stdout, stderr = self._run_kubectl_guest(
                    cluster_id,
                    ["get", "apps.catalog.cattle.io", release_name,
                     "-n", namespace, "-o", "json"]
                )
                if rc == 0 and stdout.strip():
                    data = json.loads(stdout)
                    info = data.get("spec", {}).get("info", {})
                    status = info.get("status", "")
                    if status == "deployed":
                        logging(f"Chart app {release_name} is deployed")
                        return data

                    if iteration % 10 == 0:
                        logging(f"Chart app {release_name} status: "
                                f"{status}")
                elif iteration % 10 == 0:
                    logging(f"Chart app {release_name} not found yet: "
                            f"{stderr.strip()[:200]}", level="WARNING")
            except Exception as e:
                if iteration % 10 == 0:
                    logging(f"Error checking chart app: {e}",
                            level="WARNING")

            iteration += 1
            time.sleep(retry_interval)

        raise Exception(
            f"Timeout waiting for chart app {release_name} to be ready"
        )
