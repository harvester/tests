""" Setting Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Setting implementations"""

    @abstractmethod
    def get(self, setting_id):
        """Get setting details"""
        pass

    @abstractmethod
    def enable(self, setting_id):
        """Enable a setting"""
        pass
