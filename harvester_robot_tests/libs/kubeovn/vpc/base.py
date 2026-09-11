"""
Base class for VPC operation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def get_vpc(self, vpc_name):
        pass
