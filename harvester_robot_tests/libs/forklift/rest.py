"""
Forklift Component: REST Implementation

Layer 4: Component and its implementation

Forklift objects are not exposed through the Harvester REST API, so every
method falls back to the CRD strategy.
"""

from .base import Base


class Rest(Base):
    """REST implementation for Forklift operations"""

    def __init__(self):
        super().__init__()

    def get_virt_v2v_image(self):
        return super().get_virt_v2v_image()

    def start_image_probe(self, image, pod_name):
        return super().start_image_probe(image, pod_name)

    def exec_in_probe(self, pod_name, command, timeout):
        return super().exec_in_probe(pod_name, command, timeout)

    def delete_probe(self, pod_name):
        return super().delete_probe(pod_name)

    def get_provider(self, name):
        return super().get_provider(name)

    def create_plan(self, name, source_provider, storage_map, network_map,
                    vm_name, target_namespace):
        return super().create_plan(name, source_provider, storage_map, network_map,
                                   vm_name, target_namespace)

    def start_migration(self, name, plan_name):
        return super().start_migration(name, plan_name)

    def get_migration(self, name):
        return super().get_migration(name)

    def delete_plan(self, name):
        return super().delete_plan(name)

    def delete_migration(self, name):
        return super().delete_migration(name)

    def get_plan(self, name):
        return super().get_plan(name)

    def delete_plan_volumes(self, plan_name, namespace):
        return super().delete_plan_volumes(plan_name, namespace)
