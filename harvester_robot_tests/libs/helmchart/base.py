"""
Abstract base class for HelmChart operations.
Layer 4: defines the interface that CRD and REST implementations must satisfy.
"""
from abc import ABC, abstractmethod
from constant import DEFAULT_TIMEOUT_LONG


class Base(ABC):
    """Abstract base for HelmChart implementations."""

    @abstractmethod
    def create(self, name, namespace, spec):
        """Create a HelmChart resource."""

    @abstractmethod
    def wait_for_deployed(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        """Wait until the HelmChart is fully deployed."""

    @abstractmethod
    def delete(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        """Delete a HelmChart resource and wait until it is gone."""
