"""
Addon CRD Implementation - Kubernetes API operations
Layer 4: Makes actual kubectl/K8s API calls for addon operations
"""

import time
import subprocess
import signal
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cr, patch_cr
from constant import (
    DEFAULT_TIMEOUT,
    HARVESTER_API_GROUP,
    HARVESTER_API_VERSION,
    HARVESTER_NAMESPACE,
    ADDON_PLURAL,
)
from utility.utility import logging, get_retry_count_and_interval
from addon.base import Base


class CRD(Base):
    """
    CRD implementation for Addon operations using Kubernetes API
    """

    def __init__(self):
        """Initialize Kubernetes client"""
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.addon_group = HARVESTER_API_GROUP
        self.addon_version = HARVESTER_API_VERSION
        self.addon_plural = ADDON_PLURAL
        self.port_forward_process = None
        # Common namespaces where addons are located
        self.addon_namespaces = [
            'cattle-monitoring-system',
            'cattle-logging-system',
            'harvester-system',
            'kube-system'
        ]

    def _find_addon_namespace(self, addon_name):
        """
        Find the namespace where the addon is located
        
        Args:
            addon_name: Name of the addon
            
        Returns:
            str: Namespace of the addon, or None if not found
        """
        # Try each known addon namespace
        for namespace in self.addon_namespaces:
            try:
                addon = self.custom_api.get_namespaced_custom_object(
                    group=self.addon_group,
                    version=self.addon_version,
                    namespace=namespace,
                    plural=self.addon_plural,
                    name=addon_name
                )
                if addon:
                    logging(f"Found addon {addon_name} in namespace {namespace}")
                    return namespace
            except ApiException as e:
                if e.status == 404:
                    # Addon not in this namespace, try next one
                    continue
                else:
                    # Some other error, log it but continue searching
                    logging(f"Error checking namespace {namespace}: {e}", level='WARNING')
                    continue
        
        logging(f"Addon {addon_name} not found in any known namespace", level='WARNING')
        return None

    def get_addon(self, addon_name):
        """
        Get addon details

        Args:
            addon_name: Name of the addon

        Returns:
            dict: Addon object
        """
        # First find which namespace the addon is in
        namespace = self._find_addon_namespace(addon_name)
        if not namespace:
            logging(f"Addon {addon_name} not found", level='WARNING')
            return None
            
        try:
            addon = get_cr(
                group=self.addon_group,
                version=self.addon_version,
                namespace=namespace,
                plural=self.addon_plural,
                name=addon_name
            )
            logging(f"Retrieved addon {addon_name}")
            return addon
        except ApiException as e:
            if e.status == 404:
                logging(f"Addon {addon_name} not found", level='WARNING')
                return None
            raise Exception(f"Failed to get addon {addon_name}: {e}")

    def enable_addon(self, addon_name):
        """
        Enable an addon

        Args:
            addon_name: Name of the addon to enable
        """
        logging(f"Enabling addon {addon_name}")
        
        # First find which namespace the addon is in
        namespace = self._find_addon_namespace(addon_name)
        if not namespace:
            raise Exception(f"Addon {addon_name} not found in any namespace")
        
        patch_body = {
            "spec": {
                "enabled": True
            }
        }
        try:
            patch_cr(
                group=self.addon_group,
                version=self.addon_version,
                namespace=namespace,
                plural=self.addon_plural,
                name=addon_name,
                body=patch_body
            )
            logging(f"Addon {addon_name} enable request sent")
        except ApiException as e:
            raise Exception(f"Failed to enable addon {addon_name}: {e}")

    def disable_addon(self, addon_name):
        """
        Disable an addon

        Args:
            addon_name: Name of the addon to disable
        """
        logging(f"Disabling addon {addon_name}")
        
        # First find which namespace the addon is in
        namespace = self._find_addon_namespace(addon_name)
        if not namespace:
            raise Exception(f"Addon {addon_name} not found in any namespace")
        
        patch_body = {
            "spec": {
                "enabled": False
            }
        }
        try:
            patch_cr(
                group=self.addon_group,
                version=self.addon_version,
                namespace=namespace,
                plural=self.addon_plural,
                name=addon_name,
                body=patch_body
            )
            logging(f"Addon {addon_name} disable request sent")
        except ApiException as e:
            raise Exception(f"Failed to disable addon {addon_name}: {e}")

    def wait_for_addon_enabled(self, addon_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for addon to be enabled

        Args:
            addon_name: Name of the addon
            timeout: Timeout in seconds
        """
        logging(f"Waiting for addon {addon_name} to be enabled (timeout: {timeout}s)")
        retry_count, retry_interval = get_retry_count_and_interval()
        max_retries = int(timeout / retry_interval)

        for i in range(max_retries):
            try:
                addon = self.get_addon(addon_name)
                if addon:
                    spec_enabled = addon.get('spec', {}).get('enabled', False)
                    status = addon.get('status', {})
                    status_conditions = status.get('conditions', [])

                    # Check if enabled in spec
                    if spec_enabled:
                        # Check deployment status
                        completed = False
                        for condition in status_conditions:
                            if condition.get('type') == 'Completed':
                                if condition.get('status') == 'True':
                                    completed = True
                                    break

                        if completed:
                            logging(f"Addon {addon_name} is enabled and deployed")
                            return True

                logging(f"Addon {addon_name} not yet enabled, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            except Exception as e:
                logging(f"Error checking addon status: {e}", level='WARNING')
                time.sleep(retry_interval)

        raise TimeoutError(
            f"Timeout waiting for addon {addon_name} to be enabled after {timeout}s"
        )

    def wait_for_addon_disabled(self, addon_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for addon to be disabled

        Args:
            addon_name: Name of the addon
            timeout: Timeout in seconds
        """
        logging(f"Waiting for addon {addon_name} to be disabled (timeout: {timeout}s)")
        retry_count, retry_interval = get_retry_count_and_interval()
        max_retries = int(timeout / retry_interval)

        for i in range(max_retries):
            try:
                addon = self.get_addon(addon_name)
                if addon:
                    spec_enabled = addon.get('spec', {}).get('enabled', False)

                    if not spec_enabled:
                        logging(f"Addon {addon_name} is disabled")
                        return True

                logging(f"Addon {addon_name} not yet disabled, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            except Exception as e:
                logging(f"Error checking addon status: {e}", level='WARNING')
                time.sleep(retry_interval)

        raise TimeoutError(
            f"Timeout waiting for addon {addon_name} to be disabled after {timeout}s"
        )

    def get_addon_status(self, addon_name):
        """
        Get addon status

        Args:
            addon_name: Name of the addon

        Returns:
            dict: Addon status
        """
        addon = self.get_addon(addon_name)
        if addon:
            return addon.get('status', {})
        return {}

    def is_addon_enabled(self, addon_name):
        """
        Check if addon is enabled

        Args:
            addon_name: Name of the addon

        Returns:
            bool: True if addon is enabled, False otherwise
        """
        addon = self.get_addon(addon_name)
        if addon:
            return addon.get('spec', {}).get('enabled', False)
        return False

    def wait_for_pods_running(self, namespace, label_selector, timeout=DEFAULT_TIMEOUT):
        """
        Wait for pods to be running in a namespace

        Args:
            namespace: Kubernetes namespace
            label_selector: Label selector to filter pods
            timeout: Timeout in seconds
        """
        logging(f"Waiting for pods with selector '{label_selector}' in namespace '{namespace}' to be running")
        retry_count, retry_interval = get_retry_count_and_interval()
        max_retries = int(timeout / retry_interval)

        for i in range(max_retries):
            try:
                pods = self.core_api.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector
                )

                if len(pods.items) == 0:
                    logging(f"No pods found with selector '{label_selector}', retrying... ({i+1}/{max_retries})")
                    time.sleep(retry_interval)
                    continue

                all_running = True
                for pod in pods.items:
                    if pod.status.phase != 'Running':
                        all_running = False
                        break

                    # Check if all containers are ready
                    if pod.status.container_statuses:
                        for container_status in pod.status.container_statuses:
                            if not container_status.ready:
                                all_running = False
                                break

                if all_running:
                    logging(f"All pods with selector '{label_selector}' are running")
                    return True

                logging(f"Pods not yet all running, retrying... ({i+1}/{max_retries})")
                time.sleep(retry_interval)

            except ApiException as e:
                logging(f"Error listing pods: {e}", level='WARNING')
                time.sleep(retry_interval)

        raise TimeoutError(
            f"Timeout waiting for pods with selector '{label_selector}' to be running after {timeout}s"
        )

    def port_forward(self, namespace, pod_name, local_port, remote_port):
        """
        Port forward to a pod

        Args:
            namespace: Kubernetes namespace
            pod_name: Name of the pod
            local_port: Local port to forward to
            remote_port: Remote port on the pod
        """
        logging(f"Port forwarding {local_port} -> {namespace}/{pod_name}:{remote_port}")

        # Stop any existing port forward
        self.stop_port_forward()

        # Start port forward using kubectl
        cmd = [
            'kubectl', 'port-forward',
            '-n', namespace,
            pod_name,
            f'{local_port}:{remote_port}'
        ]

        try:
            self.port_forward_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
            )
            # Give it time to establish
            time.sleep(2)
            logging(f"Port forward established")
        except Exception as e:
            raise Exception(f"Failed to establish port forward: {e}")

    def stop_port_forward(self):
        """Stop port forwarding"""
        if self.port_forward_process:
            logging("Stopping port forward")
            try:
                self.port_forward_process.terminate()
                self.port_forward_process.wait(timeout=5)
            except Exception as e:
                logging(f"Error stopping port forward: {e}", level='WARNING')
                try:
                    self.port_forward_process.kill()
                except Exception as kill_err:
                    logging(f"Error force-killing port forward process: {kill_err}", level='WARNING')
            finally:
                self.port_forward_process = None

    def query_prometheus(self, query, prometheus_url='http://localhost:9090'):
        """
        Query Prometheus for metrics

        Args:
            query: PromQL query string
            prometheus_url: Prometheus URL (default: http://localhost:9090)

        Returns:
            dict: Query result
        """
        import requests
        
        logging(f'Querying Prometheus: {query}')
        try:
            response = requests.get(
                f'{prometheus_url}/api/v1/query',
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') != 'success':
                error_msg = result.get('error', result)
                raise Exception(f"Prometheus query failed: {error_msg}")
            
            logging(f'Prometheus query successful')
            return result
        except Exception as e:
            raise Exception(f"Failed to query Prometheus: {e}")

    def verify_prometheus_metric_exists(self, query, prometheus_url='http://localhost:9090', retries=3, retry_interval=5):
        """
        Verify that a Prometheus metric exists with retry logic

        Args:
            query: PromQL query string
            prometheus_url: Prometheus URL (default: http://localhost:9090)
            retries: Number of retry attempts (default: 3)
            retry_interval: Seconds to wait between retries (default: 5)

        Returns:
            bool: True if metric exists and has data

        Raises:
            AssertionError: If the metric query succeeds but returns no data after all retries
            Exception: If there is an error querying Prometheus
        """
        logging(f'Verifying Prometheus metric: {query}')
        
        for attempt in range(retries):
            try:
                result = self.query_prometheus(query, prometheus_url)
                data = result.get('data', {}).get('result', [])
                
                if len(data) > 0:
                    logging(f'Metric {query} exists with {len(data)} results')
                    return True
                else:
                    if attempt < retries - 1:
                        logging(f'Metric {query} has no data, retrying in {retry_interval}s... ({attempt+1}/{retries})')
                        time.sleep(retry_interval)
                    else:
                        logging(f'Metric {query} has no data after {retries} attempts', level='WARNING')
                        raise AssertionError(f"Prometheus metric '{query}' has no data (empty result set)")
            except AssertionError:
                raise
            except Exception as e:
                if attempt < retries - 1:
                    logging(f'Error querying metric {query}, retrying... ({attempt+1}/{retries}): {e}', level='WARNING')
                    time.sleep(retry_interval)
                else:
                    logging(f'Failed to verify metric {query}: {e}', level='ERROR')
                    raise Exception(f"Error verifying Prometheus metric '{query}': {e}")
        
        return False
