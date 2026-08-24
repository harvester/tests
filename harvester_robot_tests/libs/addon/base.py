"""
Base class for Addon operations
"""
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence


def to_plain_containers(obj):
    """Recursively convert an object tree to built-in dicts/lists.

    Robot Framework's `Create Dictionary` returns a DotDict (an OrderedDict
    subclass). PyYAML has no representer for it, so dumping one does not fail -
    it silently emits a `!!python/object/apply:robot.utils.dotdict.DotDict` tag,
    which would land in an addon's valuesContent and break the chart. Anything
    written back as YAML must be normalised through here first.
    """
    if isinstance(obj, Mapping):
        return {key: to_plain_containers(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)) or (
        isinstance(obj, Sequence) and not isinstance(obj, (str, bytes))
    ):
        return [to_plain_containers(item) for item in obj]
    return obj


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
