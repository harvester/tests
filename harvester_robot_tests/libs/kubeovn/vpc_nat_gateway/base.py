"""
Base class for VPC NAT Gateway operations
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get(self, name):
        pass

    @abstractmethod
    def create(self, name, **kwargs):
        pass

    @abstractmethod
    def delete(self, name, **kwargs):
        pass

    @abstractmethod
    def cleanup(self):
        pass
