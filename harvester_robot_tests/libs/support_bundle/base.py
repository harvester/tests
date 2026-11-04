"""
Abstract base class for SupportBundle operations.
Layer 4: defines the interface that CRD and REST implementations must satisfy.
"""
from abc import ABC, abstractmethod
from constant import HARVESTER_NAMESPACE


class Base(ABC):
    """Abstract base for SupportBundle implementations."""

    @abstractmethod
    def create(self, name, description, namespace=HARVESTER_NAMESPACE):
        """Create a SupportBundle, which starts generating right away."""

    @abstractmethod
    def delete(self, name, namespace=HARVESTER_NAMESPACE):
        """Delete a SupportBundle, ignoring when it is already gone."""
