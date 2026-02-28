"""
Addon Keywords - creates Addon() instance and delegates - NO direct API calls!
Layer 3: Keyword wrappers for Robot Framework
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from utility.utility import logging  # noqa E402
from addon import Addon  # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402


class addon_keywords:
    """Addon keyword wrapper - creates Addon component and delegates"""

    def __init__(self):
        """Initialize addon keywords with lazy loading"""
        self._addon = None

    @property
    def addon(self):
        """Lazy initialize addon to allow API client setup first"""
        if self._addon is None:
            self._addon = Addon()
        return self._addon

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
        return self.addon.query_prometheus(query, prometheus_url)

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
        """
        logging(f'Verifying Prometheus metric: {query}')
        return self.addon.verify_prometheus_metric_exists(query, prometheus_url, retries, retry_interval)

    def restore_addon_state(self, addon_name, initial_state):
        """
        Restore addon to its initial state

        Args:
            addon_name: Name of the addon
            initial_state: Initial state (True for enabled, False for disabled)
        """
        logging(f'Restoring addon {addon_name} to initial state: {initial_state}')
        
        # Handle case where initial_state might be None
        if initial_state is None:
            logging(f'Initial state is None, skipping restore for addon {addon_name}')
            return
        
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
