"""
Base class for Pod operations.
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Abstract base for Pod implementations."""

    @abstractmethod
    def create(self, pod_name, namespace, spec):
        """Create a pod from a spec dict."""
        pass

    @abstractmethod
    def delete_if_exists(self, pod_name, namespace):
        """Delete a pod if it exists; silently ignores 404."""
        pass

    @abstractmethod
    def wait_for_succeeded(self, pod_name, namespace, timeout):
        """Wait until the pod reaches the Succeeded phase."""
        pass

    @abstractmethod
    def get_logs(self, pod_name, namespace):
        """Return the full log output of a pod as a string."""
        pass
