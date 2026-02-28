"""
Base class for Addon operations
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Addon implementations"""

    @abstractmethod
    def get_addon(self, addon_name):
        """Get addon details"""
        pass

    @abstractmethod
    def enable_addon(self, addon_name):
        """Enable an addon"""
        pass

    @abstractmethod
    def disable_addon(self, addon_name):
        """Disable an addon"""
        pass

    @abstractmethod
    def wait_for_addon_enabled(self, addon_name, timeout):
        """Wait for addon to be enabled"""
        pass

    @abstractmethod
    def wait_for_addon_disabled(self, addon_name, timeout):
        """Wait for addon to be disabled"""
        pass

    @abstractmethod
    def get_addon_status(self, addon_name):
        """Get addon status"""
        pass

    @abstractmethod
    def is_addon_enabled(self, addon_name):
        """Check if addon is enabled"""
        pass

    @abstractmethod
    def wait_for_pods_running(self, namespace, label_selector, timeout):
        """Wait for pods to be running in a namespace"""
        pass

    @abstractmethod
    def port_forward(self, namespace, pod_name, local_port, remote_port):
        """Port forward to a pod"""
        pass

    @abstractmethod
    def stop_port_forward(self):
        """Stop port forwarding"""
        pass

    @abstractmethod
    def query_prometheus(self, query, prometheus_url):
        """Query Prometheus for metrics"""
        pass

    @abstractmethod
    def verify_prometheus_metric_exists(self, query, prometheus_url, retries=3, retry_interval=5):
        """Verify that a Prometheus metric exists with retry logic"""
        pass
