"""
Base class for KubeOVN Subnet
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def create_subnet(self, name, **kwargs):
        pass

    @abstractmethod
    def get(self, name):
        pass

    @abstractmethod
    def delete(self, name):
        pass
