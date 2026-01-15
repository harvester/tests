"""
Addon Keywords - creates Addon() instance and delegates - NO direct API calls!
Layer 3: Keyword wrappers for Robot Framework
"""

import requests
from utility.utility import logging
from addon import Addon
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG


class addon_keywords:
    """Addon keyword wrapper - creates Addon component and delegates"""

    def __init__(self):
        """Initialize addon keywords"""
        self.addon = Addon()

    def get_addon(self, addon_name):
        """
        Get addon details

        Args:
            addon_name: Name of the addon

        Returns:
            dict: Addon object
        """
        logging(f'Getting addon {addon_name}')
        return self.addon.get_addon(addon_name)

    def get_addon_initial_state(self, addon_name):
        """
        Get initial state of addon (enabled/disabled)

        Args:
            addon_name: Name of the addon

        Returns:
            bool: True if addon is enabled, False otherwise
        """
        logging(f'Getting initial state of addon {addon_name}')
        return self.addon.is_addon_enabled(addon_name)

    def enable_addon(self, addon_name):
        """
        Enable an addon

        Args:
            addon_name: Name of the addon to enable
        """
        logging(f'Enabling addon {addon_name}')
        self.addon.enable_addon(addon_name)

    def disable_addon(self, addon_name):
        """
        Disable an addon

        Args:
            addon_name: Name of the addon to disable
        """
        logging(f'Disabling addon {addon_name}')
        self.addon.disable_addon(addon_name)

    def wait_for_addon_enabled(self, addon_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for addon to be enabled

        Args:
            addon_name: Name of the addon
            timeout: Timeout in seconds
        """
        logging(f'Waiting for addon {addon_name} to be enabled')
        self.addon.wait_for_addon_enabled(addon_name, int(timeout))

    def wait_for_addon_disabled(self, addon_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for addon to be disabled

        Args:
            addon_name: Name of the addon
            timeout: Timeout in seconds
        """
        logging(f'Waiting for addon {addon_name} to be disabled')
        self.addon.wait_for_addon_disabled(addon_name, int(timeout))

    def get_addon_status(self, addon_name):
        """
        Get addon status

        Args:
            addon_name: Name of the addon

        Returns:
            dict: Addon status
        """
        logging(f'Getting addon {addon_name} status')
        return self.addon.get_addon_status(addon_name)

    def is_addon_enabled(self, addon_name):
        """
        Check if addon is enabled

        Args:
            addon_name: Name of the addon

        Returns:
            bool: True if addon is enabled, False otherwise
        """
        return self.addon.is_addon_enabled(addon_name)

    def wait_for_monitoring_pods_running(self, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        """
        Wait for monitoring pods to be running

        Args:
            namespace: Kubernetes namespace where monitoring pods are deployed
            timeout: Timeout in seconds
        """
        logging(f'Waiting for monitoring pods in namespace {namespace} to be running')
        # Wait for Prometheus pods
        self.addon.wait_for_pods_running(
            namespace,
            'app.kubernetes.io/name=prometheus',
            int(timeout)
        )
        # Wait for Grafana pods
        self.addon.wait_for_pods_running(
            namespace,
            'app.kubernetes.io/name=grafana',
            int(timeout)
        )

    def port_forward_to_prometheus(self, namespace, pod_name, local_port=9090):
        """
        Port forward to Prometheus pod

        Args:
            namespace: Kubernetes namespace
            pod_name: Name of the Prometheus pod
            local_port: Local port to forward to (default: 9090)
        """
        logging(f'Port forwarding to Prometheus pod {pod_name}')
        self.addon.port_forward(namespace, pod_name, local_port, 9090)

    def stop_port_forward(self):
        """Stop port forwarding"""
        logging('Stopping port forward')
        self.addon.stop_port_forward()

    def query_prometheus(self, query, prometheus_url='http://localhost:9090'):
        """
        Query Prometheus for metrics

        Args:
            query: PromQL query string
            prometheus_url: Prometheus URL (default: http://localhost:9090)

        Returns:
            dict: Query result
        """
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
                raise Exception(f"Prometheus query failed: {result}")
            
            logging(f'Prometheus query successful')
            return result
        except Exception as e:
            raise Exception(f"Failed to query Prometheus: {e}")

    def verify_prometheus_metric_exists(self, query, prometheus_url='http://localhost:9090'):
        """
        Verify that a Prometheus metric exists

        Args:
            query: PromQL query string
            prometheus_url: Prometheus URL (default: http://localhost:9090)

        Returns:
            bool: True if metric exists and has data
        """
        logging(f'Verifying Prometheus metric: {query}')
        try:
            result = self.query_prometheus(query, prometheus_url)
            data = result.get('data', {}).get('result', [])
            
            if len(data) > 0:
                logging(f'Metric {query} exists with {len(data)} results')
                return True
            else:
                logging(f'Metric {query} has no data', level='WARNING')
                return False
        except Exception as e:
            logging(f'Failed to verify metric {query}: {e}', level='ERROR')
            return False

    def restore_addon_state(self, addon_name, initial_state):
        """
        Restore addon to its initial state

        Args:
            addon_name: Name of the addon
            initial_state: Initial state (True for enabled, False for disabled)
        """
        logging(f'Restoring addon {addon_name} to initial state: {initial_state}')
        current_state = self.addon.is_addon_enabled(addon_name)
        
        if current_state != initial_state:
            if initial_state:
                self.enable_addon(addon_name)
                self.wait_for_addon_enabled(addon_name)
            else:
                self.disable_addon(addon_name)
                self.wait_for_addon_disabled(addon_name)
        else:
            logging(f'Addon {addon_name} already in desired state')
