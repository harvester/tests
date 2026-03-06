"""
Rancher REST Implementation - Harvester and Rancher REST API operations
Layer 4: Makes actual REST API calls for Rancher integration operations
"""

import os
import time
import requests
import json
from utility.utility import logging, get_retry_count_and_interval, get_harvester_api_client
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG, DEFAULT_NAMESPACE
from rancher.base import Base


class Rest(Base):
    """
    REST implementation for Rancher Integration operations using REST APIs

    This implementation uses both Harvester and Rancher REST APIs.
    """

    def __init__(self):
        """Initialize REST clients"""
        self.harvester_api = get_harvester_api_client()

        # Rancher API client (initialize on-demand)
        self.rancher_endpoint = os.getenv("RANCHER_ENDPOINT", "")
        self.rancher_token = None
        self.rancher_session = None

    def _authenticate_rancher(self, rancher_endpoint=None):
        """Authenticate with Rancher and get token"""
        if self.rancher_token and self.rancher_session:
            return  # Already authenticated

        if not rancher_endpoint:
            rancher_endpoint = self.rancher_endpoint

        # Try to get credentials from Robot Framework variables first, then fall back to env vars
        try:
            from robot.libraries.BuiltIn import BuiltIn
            username = BuiltIn().get_variable_value("${RANCHER_USERNAME}", "admin")
            password = BuiltIn().get_variable_value("${RANCHER_PASSWORD}", "password1234")
        except Exception:
            # Fall back to environment variables if not running in Robot Framework context
            username = os.getenv("RANCHER_USERNAME", "admin")
            password = os.getenv("RANCHER_PASSWORD", "password1234")

        logging(f"Authenticating with Rancher at {rancher_endpoint} as user {username}")

        session = requests.Session()
        session.verify = False
        session.headers.update({"Content-Type": "application/json"})

        from urllib.parse import urljoin
        url = urljoin(rancher_endpoint, "v3-public/localProviders/local?action=login")
        logging(f"Auth URL: {url}")

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

        session.headers.update({"Authorization": f"Bearer {token}"})

        self.rancher_token = token
        self.rancher_session = session
        logging("Successfully authenticated with Rancher")

    def _rancher_request(self, method, path, data=None):
        """Make request to Rancher API"""
        # Ensure authenticated
        self._authenticate_rancher()

        url = f"{self.rancher_endpoint.rstrip('/')}/{path.lstrip('/')}"
        logging(f"Rancher API request: {method} {url}")

        try:
            if method.upper() == "GET":
                response = self.rancher_session.get(url)
            elif method.upper() == "POST":
                response = self.rancher_session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.rancher_session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.rancher_session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text

            return response.status_code, response_data
        except Exception as e:
            raise Exception(f"Rancher API request failed: {e}")

    def create_harvester_mgmt_cluster(self, cluster_name):
        """Create Harvester management cluster entry in Rancher (Import Existing)"""
        logging(f"Creating Harvester management cluster entry: {cluster_name}")

        payload = {
            "type": "provisioning.cattle.io.cluster",
            "metadata": {
                "name": cluster_name,
                "namespace": "fleet-default",
                "labels": {
                    "provider.cattle.io": "harvester"
                }
            },
            "spec": {}
        }

        code, data = self._rancher_request(
            "POST",
            "v1/provisioning.cattle.io.clusters",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create Harvester mgmt cluster: {code}, {data}")

        logging(f"Created Harvester management cluster: {cluster_name}")
        return data

    def get_harvester_mgmt_cluster(self, cluster_name):
        """Get Harvester management cluster details"""
        logging(f"Getting Harvester management cluster: {cluster_name}")

        code, data = self._rancher_request(
            "GET",
            f"v1/provisioning.cattle.io.clusters/fleet-default/{cluster_name}"
        )

        if code == 404:
            logging(f"Harvester mgmt cluster {cluster_name} not found")
            return None
        elif code != 200:
            raise Exception(f"Failed to get Harvester mgmt cluster: {code}, {data}")

        return data

    def delete_harvester_mgmt_cluster(self, cluster_name):
        """Delete Harvester management cluster entry"""
        logging(f"Deleting Harvester management cluster: {cluster_name}")

        code, data = self._rancher_request(
            "DELETE",
            f"v1/provisioning.cattle.io.clusters/fleet-default/{cluster_name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete Harvester mgmt cluster: {code}, {data}")

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

    def get_cluster_registration_url(self, cluster_id, rancher_endpoint=None, timeout=300):
        """Get cluster registration URL for importing Harvester"""
        logging(f"Getting cluster registration URL for cluster: {cluster_id}")

        # Authenticate first
        self._authenticate_rancher(rancher_endpoint)

        logging(f"Polling Rancher API for registration token: {cluster_id}:default-token")

        # Poll for the registration token to appear
        retry_count, retry_interval = get_retry_count_and_interval()
        end_time = time.time() + int(timeout)
        attempt = 0

        while time.time() < end_time:
            attempt += 1
            code, data = self._rancher_request(
                "GET",
                f"v3/clusterRegistrationTokens/{cluster_id}:default-token"
            )

            # Log every 5 attempts to show progress
            if attempt % 5 == 1 or code not in [200, 404]:
                logging(f"Attempt {attempt}: Response status {code}")

            if code == 200:
                manifest_url = data.get("manifestUrl")
                if manifest_url:
                    logging(f"Got cluster registration URL: {manifest_url}")
                    return manifest_url
                else:
                    if attempt % 5 == 1:
                        logging("manifestUrl not yet available in response, waiting...")
            elif code == 404:
                if attempt % 5 == 1:
                    logging("Registration token not yet created, waiting...")
            else:
                logging(f"Unexpected response {code}: {data}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(
            f"Timeout waiting for cluster registration URL for {cluster_id} "
            f"after {attempt} attempts"
        )

    def set_cluster_registration_url(self, url):
        """Set cluster-registration-url setting in Harvester

        The value must be in JSON format matching Harvester structure:
        {'url': '...', 'insecureSkipTLSVerify': true/false}
        """
        logging(f"Setting cluster-registration-url to: {url}")

        # Format the value as JSON object (matching Harvester's default structure)
        if url:
            value_obj = {"url": url, "insecureSkipTLSVerify": True}
            value = json.dumps(value_obj)
        else:
            value = '{"url":"","insecureSkipTLSVerify":false}'

        # Get current setting first
        code, data = self.harvester_api.settings.get("cluster-registration-url")
        if code != 200:
            raise Exception(f"Failed to get cluster-registration-url setting: {code}, {data}")

        # Update the value field with the JSON string
        data["value"] = value

        # Use the API's internal _put method directly
        path = f"apis/{self.harvester_api.API_VERSION}/settings/cluster-registration-url"
        resp = self.harvester_api._put(path, json=data)

        if resp.status_code not in [200, 201]:
            try:
                error_data = resp.json()
            except Exception:
                error_data = resp.text
            raise Exception(
                f"Failed to set cluster-registration-url: "
                f"{resp.status_code}, {error_data}"
            )

        logging("Successfully set cluster-registration-url")

    def get_all_rke2_versions(self, rancher_endpoint=None, max_versions=None):
        """
        Get all available RKE2 versions from Rancher.

        Args:
            rancher_endpoint: Rancher server endpoint (uses self.rancher_api if not provided)
            max_versions: Maximum number of versions to return (None = all)

        Returns:
            List of version strings sorted by semantic version (newest first)
        """
        logging("Getting all RKE2 versions from Rancher")

        code, data = self._rancher_request("GET", "v1-rke2-release/releases")

        if code != 200:
            raise Exception(f"Failed to get RKE2 versions: {code}, {data}")

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

    def get_rke2_version(self, target_version, rancher_endpoint=None):
        """
        Get RKE2 version from Rancher that matches target version.

        Args:
            target_version: Target version prefix (e.g. 'v1.28', 'v1.29')
            rancher_endpoint: Rancher server endpoint (uses self.rancher_api if not provided)

        Returns:
            Full version string (e.g. 'v1.28.15+rke2r1')
        """
        logging(f"Getting RKE2 version for target: {target_version}")

        code, data = self._rancher_request("GET", "v1-rke2-release/releases")

        if code != 200:
            raise Exception(f"Failed to get RKE2 versions: {code}, {data}")

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

    def create_cloud_credential(self, name, kubeconfig, cluster_id):
        """Create cloud credential for Harvester"""
        logging(f"Creating cloud credential: {name}")

        payload = {
            "type": "cloudCredential",
            "name": name,
            "harvestercredentialConfig": {
                "clusterId": cluster_id,
                "clusterType": "imported",
                "kubeconfigContent": kubeconfig
            }
        }

        code, data = self._rancher_request("POST", "v3/cloudcredentials", payload)

        if code not in [200, 201]:
            raise Exception(f"Failed to create cloud credential: {code}, {data}")

        logging(f"Created cloud credential: {name}")
        return data

    def get_cloud_credential(self, credential_id):
        """Get cloud credential details"""
        logging(f"Getting cloud credential: {credential_id}")

        code, data = self._rancher_request("GET", f"v3/cloudCredentials/{credential_id}")

        if code == 404:
            return None
        elif code != 200:
            raise Exception(f"Failed to get cloud credential: {code}, {data}")

        return data

    def delete_cloud_credential(self, credential_id):
        """Delete cloud credential"""
        logging(f"Deleting cloud credential: {credential_id}")

        code, data = self._rancher_request("DELETE", f"v3/cloudCredentials/{credential_id}")

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete cloud credential: {code}, {data}")

        logging(f"Deleted cloud credential: {credential_id}")

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

        payload = {
            "type": "provisioning.cattle.io.cluster",
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

        code, data = self._rancher_request(
            "POST",
            "v1/provisioning.cattle.io.clusters",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create RKE2 cluster: {code}, {data}")

        logging(f"Created RKE2 cluster: {name}")
        return data

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

                    # Count actual running machines via Rancher API
                    total_running = self._count_running_machines(cluster_name)

                    if (ready and updated and provisioned
                            and total_running >= total_desired > 0):
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
        """Count machines in Running phase for a given cluster via Rancher API."""
        try:
            code, data = self._rancher_request(
                "GET",
                f"v1/cluster.x-k8s.io.machines/fleet-default"
                f"?labelSelector=cluster.x-k8s.io/cluster-name={cluster_name}"
            )
            if code != 200:
                return 0
            items = data.get("data", []) if isinstance(data, dict) else []
            return sum(1 for m in items
                       if m.get("status", {}).get("phase") == "Running")
        except Exception:
            return 0

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
        """Scale RKE2 cluster by adding/removing a worker-only machine pool."""
        logging(f"Scaling RKE2 cluster {cluster_name}: worker_count={worker_count}")

        cluster = self.get_rke2_cluster(cluster_name)
        if not cluster:
            raise Exception(f"RKE2 cluster {cluster_name} not found")

        machine_pools = cluster.get("spec", {}).get("rkeConfig", {}).get("machinePools", [])

        # Remove existing worker-pool if present
        machine_pools = [p for p in machine_pools if p.get("name") != "worker-pool"]

        if int(worker_count) > 0:
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

        # Update the cluster via PUT
        cluster["spec"]["rkeConfig"]["machinePools"] = machine_pools

        code, data = self._rancher_request(
            "PUT",
            f"v1/provisioning.cattle.io.clusters/fleet-default/{cluster_name}",
            cluster
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to scale RKE2 cluster: {code}, {data}")

        logging(f"Scaled RKE2 cluster {cluster_name} worker pool to {worker_count}")

    def upgrade_rke2_cluster(self, cluster_name, new_k8s_version):
        """Upgrade RKE2 cluster to a new Kubernetes version."""
        logging(f"Upgrading RKE2 cluster {cluster_name} to {new_k8s_version}")

        cluster = self.get_rke2_cluster(cluster_name)
        if not cluster:
            raise Exception(f"RKE2 cluster {cluster_name} not found")

        cluster["spec"]["kubernetesVersion"] = new_k8s_version

        code, data = self._rancher_request(
            "PUT",
            f"v1/provisioning.cattle.io.clusters/fleet-default/{cluster_name}",
            cluster
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to upgrade RKE2 cluster: {code}, {data}")

        logging(f"Triggered upgrade of RKE2 cluster {cluster_name} to {new_k8s_version}")

    def create_harvester_config(self, name, cpus, mems, disks, image_id,
                                network_id, ssh_user, user_data):
        """Create Harvester config for RKE2 node template"""
        logging(f"Creating Harvester config: {name}")

        import base64

        # Build diskInfo and networkInfo as JSON structures
        import json
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

        payload = {
            "type": "rke-machine-config.cattle.io.harvesterconfig",
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

        code, data = self._rancher_request(
            "POST",
            "v1/rke-machine-config.cattle.io.harvesterconfigs",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create Harvester config: {code}, {data}")

        logging(f"Created Harvester config: {name}")
        return data

    def generate_kubeconfig(self, cluster_id, cluster_name):
        """Generate full-access kubeconfig for Harvester cluster.

        Uses Rancher's generateKubeconfig action to get a kubeconfig with
        full access to the Harvester cluster. Used for cloud credentials.
        """
        logging(f"Generating kubeconfig for cluster: {cluster_name}")

        code, data = self._rancher_request(
            "POST",
            f"v3/clusters/{cluster_id}?action=generateKubeconfig"
        )

        if code != 200:
            raise Exception(f"Failed to generate kubeconfig: {code}, {data}")

        logging("Generated kubeconfig for cluster")
        return data.get("config", "")

    def generate_cloud_provider_kubeconfig(self, cluster_id, cluster_name):
        """Generate cloud provider kubeconfig via Harvester kubeconfig API.

        Uses the Harvester-specific endpoint to generate a kubeconfig with
        the external Rancher URL and limited cloudprovider role. This is
        used for the cloud provider secret inside the guest VM.
        """
        logging(f"Generating cloud provider kubeconfig for cluster: {cluster_name}")

        code, data = self._rancher_request(
            "POST",
            f"k8s/clusters/{cluster_id}/v1/harvester/kubeconfig",
            {
                "clusterRoleName": "harvesterhci.io:cloudprovider",
                "namespace": "default",
                "serviceAccountName": cluster_name
            }
        )

        if code != 200:
            raise Exception(f"Failed to generate harvester kubeconfig: {code}, {data}")

        # Response is a JSON-encoded string with \n escapes
        if isinstance(data, str):
            kubeconfig = data.replace("\\n", "\n").strip('"')
        else:
            kubeconfig = str(data)

        logging("Generated cloud provider kubeconfig for cluster")
        return kubeconfig

    def create_secret(self, name, data, annotations):
        """Create secret for cloud provider config"""
        logging(f"Creating secret: {name}")

        payload = {
            "type": "secret",
            "metadata": {
                "name": name,
                "namespace": "fleet-default",
                "annotations": annotations
            },
            "stringData": data
        }

        code, resp_data = self._rancher_request(
            "POST",
            "v1/secrets/fleet-default",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create secret: {code}, {resp_data}")

        logging(f"Created secret: {name}")
        return resp_data

    def create_deployment(self, cluster_id, namespace, name, image, pvc=None):
        """Create deployment in guest cluster"""
        logging(f"Creating deployment {name} in cluster {cluster_id}")

        payload = {
            "type": "apps.deployment",
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
                        "containers": [
                            {
                                "name": name,
                                "image": image,
                                "ports": [{"containerPort": 80}]
                            }
                        ]
                    }
                }
            }
        }

        if pvc:
            payload["spec"]["template"]["spec"]["volumes"] = [
                {"name": "data", "persistentVolumeClaim": {"claimName": pvc}}
            ]
            payload["spec"]["template"]["spec"]["containers"][0]["volumeMounts"] = [
                {"name": "data", "mountPath": "/data"}
            ]

        code, data = self._rancher_request(
            "POST",
            f"k8s/clusters/{cluster_id}/v1/apps.deployments/{namespace}",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create deployment: {code}, {data}")

        logging(f"Created deployment {name}")
        return data

    def get_deployment(self, cluster_id, namespace, name):
        """Get deployment details from guest cluster"""
        logging(f"Getting deployment {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "GET",
            f"k8s/clusters/{cluster_id}/v1/apps.deployments/{namespace}/{name}"
        )

        if code == 404:
            return None
        elif code != 200:
            raise Exception(f"Failed to get deployment: {code}, {data}")

        return data

    def delete_deployment(self, cluster_id, namespace, name):
        """Delete deployment from guest cluster"""
        logging(f"Deleting deployment {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "DELETE",
            f"k8s/clusters/{cluster_id}/v1/apps.deployments/{namespace}/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete deployment: {code}, {data}")

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
                    state = deployment.get("metadata", {}).get("state", {}).get("name", "")
                    if state == "active":
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
        """Create PVC in guest cluster"""
        logging(f"Creating PVC {name} in cluster {cluster_id}")

        payload = {
            "type": "persistentvolumeclaim",
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
            payload["spec"]["storageClassName"] = storage_class

        code, data = self._rancher_request(
            "POST",
            f"k8s/clusters/{cluster_id}/v1/persistentvolumeclaims/{DEFAULT_NAMESPACE}",
            payload
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create PVC: {code}, {data}")

        logging(f"Created PVC {name}")
        return data

    def get_pvc(self, cluster_id, name):
        """Get PVC details from guest cluster"""
        logging(f"Getting PVC {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "GET",
            f"k8s/clusters/{cluster_id}/v1/persistentvolumeclaims/{DEFAULT_NAMESPACE}/{name}"
        )

        if code == 404:
            return None
        elif code != 200:
            raise Exception(f"Failed to get PVC: {code}, {data}")

        return data

    def delete_pvc(self, cluster_id, name):
        """Delete PVC from guest cluster"""
        logging(f"Deleting PVC {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "DELETE",
            f"k8s/clusters/{cluster_id}/v1/persistentvolumeclaims/{DEFAULT_NAMESPACE}/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete PVC: {code}, {data}")

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
                    state = pvc.get("metadata", {}).get("state", {}).get("name", "")
                    if state == "bound":
                        logging(f"PVC {name} is bound")
                        return pvc
            except Exception as e:
                logging(f"Error checking PVC status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for PVC {name} to be bound")

    def create_lb_service(self, cluster_id, service_data):
        """Create LoadBalancer service"""
        name = service_data["metadata"]["name"]
        namespace = service_data["metadata"]["namespace"]
        logging(f"Creating LoadBalancer service {name} in cluster {cluster_id}")

        code, data = self._rancher_request(
            "POST",
            f"k8s/clusters/{cluster_id}/v1/services/{namespace}",
            service_data
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create LoadBalancer service: {code}, {data}")

        logging(f"Created LoadBalancer service {name}")
        return data

    def get_lb_service(self, cluster_id, name):
        """Get LoadBalancer service details"""
        logging(f"Getting LoadBalancer service {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "GET",
            f"k8s/clusters/{cluster_id}/v1/services/{DEFAULT_NAMESPACE}/{name}"
        )

        if code == 404:
            return None
        elif code != 200:
            raise Exception(f"Failed to get LoadBalancer service: {code}, {data}")

        return data

    def delete_lb_service(self, cluster_id, name):
        """Delete LoadBalancer service"""
        logging(f"Deleting LoadBalancer service {name} from cluster {cluster_id}")

        code, data = self._rancher_request(
            "DELETE",
            f"k8s/clusters/{cluster_id}/v1/services/{DEFAULT_NAMESPACE}/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete LoadBalancer service: {code}, {data}")

        logging(f"Deleted LoadBalancer service {name}")

    def wait_for_lb_service_ready(self, cluster_id, name, timeout=DEFAULT_TIMEOUT):
        """Wait for LoadBalancer service to be ready"""
        logging(f"Waiting for LoadBalancer service {name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        while time.time() < end_time:
            try:
                service = self.get_lb_service(cluster_id, name)
                if service:
                    state = service.get("metadata", {}).get("state", {}).get("name", "")
                    if state == "active":
                        ingress = (
                            service.get("status", {})
                            .get("loadBalancer", {})
                            .get("ingress", [])
                        )
                        if ingress and ingress[0].get("ip"):
                            logging(
                                f"LoadBalancer service {name} is ready "
                                f"with IP {ingress[0]['ip']}"
                            )
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

        Uses /k8s/clusters/{id}/api/v1/namespaces/{ns}/services/{svc}:{port}/proxy/
        which works regardless of whether the LB VIP is routable from the test runner.
        """
        proxy_path = (f"k8s/clusters/{cluster_id}/api/v1/namespaces/{namespace}/"
                      f"services/{service_name}:{port}/proxy/")
        logging(f"Querying LB via Rancher proxy: {proxy_path}")
        last_err = None
        for attempt in range(retries):
            try:
                code, data = self._rancher_request("GET", proxy_path)
                return code, data if isinstance(data, str) else str(data)
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    logging(f"LB proxy query attempt {attempt + 1}/{retries} "
                            f"failed: {e}, retrying...")
                    time.sleep(interval)
        raise Exception(f"Failed to query LB via proxy after {retries} attempts: {last_err}")

    def wait_for_harvester_deployments_ready(self, cluster_id, timeout=DEFAULT_TIMEOUT):
        """Wait for harvester-cloud-provider and harvester-csi-driver to be ready"""
        logging(f"Waiting for Harvester deployments in cluster {cluster_id}")
        deployments = ["harvester-cloud-provider", "harvester-csi-driver-controllers"]

        for deployment_name in deployments:
            self.wait_for_deployment_ready(cluster_id, "kube-system", deployment_name, timeout)

        logging("All Harvester deployments are ready")

    def create_vlan_network(self, name, vlan_id, cluster_network):
        """Create VLAN network"""
        logging(f"Creating VLAN network: {name}")

        code, data = self.harvester_api.post(
            f"v1/k8s.cni.cncf.io.network-attachment-definitions/{DEFAULT_NAMESPACE}",
            data={
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
        )

        if code not in [200, 201, 409]:
            raise Exception(f"Failed to create VLAN network: {code}, {data}")

        logging(f"Created VLAN network: {name}")
        return data

    def delete_vlan_network(self, name):
        """Delete VLAN network"""
        logging(f"Deleting VLAN network: {name}")

        code, data = self.harvester_api.delete(
            f"v1/k8s.cni.cncf.io.network-attachment-definitions/{DEFAULT_NAMESPACE}/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete VLAN network: {code}, {data}")

        logging(f"Deleted VLAN network: {name}")

    def get_ip_pool(self, name):
        """Get IP pool by name, returns None if not found"""
        logging(f"Getting IP pool: {name}")
        code, data = self.harvester_api.get(
            f"v1/harvester/loadbalancer.harvesterhci.io.ippools/{name}"
        )
        if code == 404:
            return None
        if code not in [200, 201]:
            raise Exception(f"Failed to get IP pool: {code}, {data}")
        return data

    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """Create IP pool, reusing existing pool with the same name"""
        logging(f"Creating IP pool: {name}")

        existing = self.get_ip_pool(name)
        if existing:
            logging(f"IP pool {name} already exists, reusing")
            return existing

        code, data = self.harvester_api.post(
            "v1/harvester/loadbalancer.harvesterhci.io.ippools",
            data={
                "type": "loadbalancer.harvesterhci.io.ippool",
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
        )

        if code not in [200, 201, 409]:
            raise Exception(f"Failed to create IP pool: {code}, {data}")

        logging(f"Created IP pool: {name}")
        return data

    def delete_ip_pool(self, name):
        """Delete IP pool"""
        logging(f"Deleting IP pool: {name}")

        code, data = self.harvester_api.delete(
            f"v1/harvester/loadbalancer.harvesterhci.io.ippools/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete IP pool: {code}, {data}")

        logging(f"Deleted IP pool: {name}")

    def create_image(self, name, url):
        """Create image by URL"""
        logging(f"Creating image: {name}")

        code, data = self.harvester_api.post(
            f"v1/harvester/harvesterhci.io.virtualmachineimages/{DEFAULT_NAMESPACE}",
            data={
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
        )

        if code not in [200, 201]:
            raise Exception(f"Failed to create image: {code}, {data}")

        logging(f"Created image: {name}")
        return data

    def wait_for_image_ready(self, name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be ready"""
        logging(f"Waiting for image {name} to be ready")
        retry_count, retry_interval = get_retry_count_and_interval()

        end_time = time.time() + int(timeout)
        last_logged_progress = -1
        check_count = 0
        while time.time() < end_time:
            try:
                code, data = self.harvester_api.get(
                    f"v1/harvester/harvesterhci.io.virtualmachineimages/{DEFAULT_NAMESPACE}/{name}"
                )
                if code == 200:
                    progress = data.get("status", {}).get("progress", 0)
                    check_count += 1

                    if progress == 100:
                        logging(f"Image {name} is ready")
                        return data

                    # Only log if progress changed by 5% or more, or every 10th check
                    if (abs(progress - last_logged_progress) >= 5 or check_count % 10 == 1):
                        logging(f"Image {name} progress: {progress}%")
                        last_logged_progress = progress
            except Exception as e:
                logging(f"Error checking image status: {e}", level="WARNING")

            time.sleep(retry_interval)

        raise Exception(f"Timeout waiting for image {name} to be ready")

    def delete_image(self, name):
        """Delete image"""
        logging(f"Deleting image: {name}")

        code, data = self.harvester_api.delete(
            f"v1/harvester/harvesterhci.io.virtualmachineimages/{DEFAULT_NAMESPACE}/{name}"
        )

        if code not in [200, 204, 404]:
            raise Exception(f"Failed to delete image: {code}, {data}")

        logging(f"Deleted image: {name}")
