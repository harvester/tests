""" Setting Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Setting implementations"""

    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def get(self, setting_id):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def enable(self, setting_id):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def update(self, setting_id, value):
        raise NotImplementedError(self.unsupported_msg)
