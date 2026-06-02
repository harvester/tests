""" Blockdevice Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def list(self, namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get(self, name, namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def provision_longhorn_storage(self, name, engine_version, namespace):
        raise NotImplementedError(self.unsupported_msg)
