"""
Base class for KubeOVN Subnet
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def create_subnet(self, name):
        pass

    @abstractmethod
    def get_subnet(self, name):
        pass

    @abstractmethod
    def delete_subnet(self, name):
        pass
