"""
Abstract base class for resource health operations.
Layer 4: defines the interface that CRD and REST implementations must satisfy.
"""
from abc import ABC, abstractmethod
from constant import DEFAULT_TIMEOUT


class Base(ABC):
    """Abstract base for Health implementations."""

    @abstractmethod
    def component_health_exists(self, name):
        """Return True when the ComponentHealth resource exists."""

    @abstractmethod
    def get_check(self, component_health_name, check_name):
        """Return the named check of a ComponentHealth, or None when it is not raised."""

    @abstractmethod
    def wait_for_check_affects_resource(self, component_health_name, check_name,
                                        resource_name, timeout=DEFAULT_TIMEOUT):
        """Wait until the check lists the resource as affected and return the check."""
