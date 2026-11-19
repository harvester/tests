"""
Forklift Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Forklift implementations"""

    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def get_virt_v2v_image(self):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def start_image_probe(self, image, pod_name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def exec_in_probe(self, pod_name, command, timeout):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete_probe(self, pod_name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_provider(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def create_plan(self, name, source_provider, storage_map, network_map,
                    vm_name, target_namespace):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def start_migration(self, name, plan_name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_migration(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete_plan(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete_migration(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_plan(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def delete_plan_volumes(self, plan_name, namespace):
        raise NotImplementedError(self.unsupported_msg)
