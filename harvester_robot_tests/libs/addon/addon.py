"""
Addon Component - delegates to CRD or REST implementation
Layer 4: Selects implementation based on strategy

The implementation is selected based on the HARVESTER_OPERATION_STRATEGY 
environment variable. Valid values are 'crd' or 'rest'. Defaults to 'crd' if not set.
"""

import os
from constant import HarvesterOperationStrategy
from addon.rest import Rest
from addon.crd import CRD
from addon.base import Base


class Addon(Base):
    """
    Addon component that delegates to CRD or REST implementation

    The implementation is selected based on:
    - HARVESTER_OPERATION_STRATEGY environment variable ('crd' or 'rest')
    - Defaults to 'crd' if not set
    """

    def __init__(self):
        """Initialize Addon component"""
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD
        
        if self._strategy == HarvesterOperationStrategy.CRD:
            self.addon = CRD()
        else:
            self.addon = Rest()

    def get_addon(self, addon_name):
        """Get addon details - delegates to implementation"""
        return self.addon.get_addon(addon_name)

    def enable_addon(self, addon_name):
        """Enable an addon - delegates to implementation"""
        return self.addon.enable_addon(addon_name)

    def disable_addon(self, addon_name):
        """Disable an addon - delegates to implementation"""
        return self.addon.disable_addon(addon_name)

    def wait_for_addon_enabled(self, addon_name, timeout):
        """Wait for addon to be enabled - delegates to implementation"""
        return self.addon.wait_for_addon_enabled(addon_name, timeout)

    def wait_for_addon_disabled(self, addon_name, timeout):
        """Wait for addon to be disabled - delegates to implementation"""
        return self.addon.wait_for_addon_disabled(addon_name, timeout)

    def get_addon_status(self, addon_name):
        """Get addon status - delegates to implementation"""
        return self.addon.get_addon_status(addon_name)

    def is_addon_enabled(self, addon_name):
        """Check if addon is enabled - delegates to implementation"""
        return self.addon.is_addon_enabled(addon_name)

    def wait_for_pods_running(self, namespace, label_selector, timeout):
        """Wait for pods to be running - delegates to implementation"""
        return self.addon.wait_for_pods_running(namespace, label_selector, timeout)

    def port_forward(self, namespace, pod_name, local_port, remote_port):
        """Port forward to a pod - delegates to implementation"""
        return self.addon.port_forward(namespace, pod_name, local_port, remote_port)

    def stop_port_forward(self):
        """Stop port forwarding - delegates to implementation"""
        return self.addon.stop_port_forward()

    def query_prometheus(self, query, prometheus_url):
        """Query Prometheus for metrics - delegates to implementation"""
        return self.addon.query_prometheus(query, prometheus_url)

    def verify_prometheus_metric_exists(self, query, prometheus_url, retries=3, retry_interval=5):
        """Verify that a Prometheus metric exists - delegates to implementation"""
        return self.addon.verify_prometheus_metric_exists(query, prometheus_url, retries, retry_interval)
