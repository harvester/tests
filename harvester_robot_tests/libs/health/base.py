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

    @abstractmethod
    def wait_for_resource_ignored_state(self, component_health_name, check_name,
                                        resource_name, ignored, timeout=DEFAULT_TIMEOUT):
        """Wait until the affected resource is (or is no longer) marked ignored."""

    @abstractmethod
    def wait_for_check_ignored_state(self, component_health_name, check_name,
                                     ignored, timeout=DEFAULT_TIMEOUT):
        """Wait until the whole check is (or is no longer) marked ignored."""

    @abstractmethod
    def create_ignore_rule(self, name, component_health_name, check_name,
                           resources=None, expires_at=None, reason=None):
        """Create a HealthIgnoreRule. All resources of the check when resources is empty."""

    @abstractmethod
    def expire_ignore_rule(self, name):
        """Set expiresAt of the HealthIgnoreRule to a past time."""

    @abstractmethod
    def delete_ignore_rule(self, name):
        """Delete a HealthIgnoreRule."""
