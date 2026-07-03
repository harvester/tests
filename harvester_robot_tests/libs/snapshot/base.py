from abc import ABC, abstractmethod


class Base(ABC):
    """
    Abstract Snapshot base class
    """

    @abstractmethod
    def create(self, vm_name, snapshot_name, **kwargs):
        pass

    @abstractmethod
    def delete(self, snapshot_name, **kwargs):
        pass

    @abstractmethod
    def wait_ready(self, snapshot_name, **kwargs):
        pass

    @abstractmethod
    def wait_deleted(self, snapshot_name, **kwargs):
        pass
