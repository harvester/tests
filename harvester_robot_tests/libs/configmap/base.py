""" ConfigMap Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Abstract ConfigMap base class"""

    @abstractmethod
    def create(self, name, namespace, labels=None, data=None):
        """Create a config map, with the test label and the extra `labels`"""

    @abstractmethod
    def delete(self, name, namespace):
        """Delete a config map (no-op when it does not exist)"""
