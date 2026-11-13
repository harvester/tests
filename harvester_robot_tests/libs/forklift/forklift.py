"""
Forklift Component

Layer 4: Component and its implementation
"""

from utility.utility import logging
from .base import Base
from .crd import CRD
from .rest import Rest


class Forklift(Base):
    def __init__(self):
        self.crd = CRD()
        self.rest = Rest()

    def _call(self, method, *args):
        try:
            return getattr(self.crd, method)(*args)
        except NotImplementedError as e:
            logging(e)
            return getattr(self.rest, method)(*args)

    def get_virt_v2v_image(self):
        return self._call("get_virt_v2v_image")

    def start_image_probe(self, image, pod_name):
        return self._call("start_image_probe", image, pod_name)

    def exec_in_probe(self, pod_name, command, timeout):
        return self._call("exec_in_probe", pod_name, command, timeout)

    def delete_probe(self, pod_name):
        return self._call("delete_probe", pod_name)

    def get_provider(self, name):
        return self._call("get_provider", name)

    def create_plan(self, name, source_provider, storage_map, network_map,
                    vm_name, target_namespace):
        return self._call("create_plan", name, source_provider, storage_map,
                          network_map, vm_name, target_namespace)

    def start_migration(self, name, plan_name):
        return self._call("start_migration", name, plan_name)

    def get_migration(self, name):
        return self._call("get_migration", name)

    def delete_plan(self, name):
        return self._call("delete_plan", name)

    def delete_migration(self, name):
        return self._call("delete_migration", name)

    def get_plan(self, name):
        return self._call("get_plan", name)

    def delete_plan_volumes(self, plan_name, namespace):
        return self._call("delete_plan_volumes", plan_name, namespace)
