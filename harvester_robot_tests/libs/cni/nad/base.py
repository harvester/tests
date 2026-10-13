"""
Base class for CNI NetworkAttachmentDefinition operations
"""

from abc import ABC, abstractmethod


class Base(ABC):
    @abstractmethod
    def get(self, namespace, name):
        pass

    @abstractmethod
    def create(self, namespace, name, **kwargs):
        pass

    @abstractmethod
    def delete(self, namespace, name):
        pass
