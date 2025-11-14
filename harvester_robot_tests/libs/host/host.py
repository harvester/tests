"""
Host Component - delegates to Rest implementation
"""
from constant import HarvesterOperationStrategy
from host.rest import Rest
from host.crd import CRD
from host.base import Base


class Host(Base):
    # Set desired operation strategy here
    _strategy = HarvesterOperationStrategy.CRD

    def __init__(self):
        if self._strategy == HarvesterOperationStrategy.CRD:
            self.host = CRD()
        else:
            self.host = Rest()

    def list_nodes(self):
        return self.host.list_nodes()

    def get_node_count(self):
        return self.host.get_node_count()

    def get_node(self, node_name):
        return self.host.get_node(node_name)

    def get_node_by_index(self, index):
        return self.host.get_node_by_index(index)

    def get_worker_nodes(self):
        return self.host.get_worker_nodes()

    def get_control_plane_nodes(self):
        return self.host.get_control_plane_nodes()

    def get_node_status(self, node_name):
        return self.host.get_node_status(node_name)

    def is_node_ready(self, node_name):
        return self.host.is_node_ready(node_name)

    def wait_for_node_ready(self, node_name, timeout):
        return self.host.wait_for_node_ready(node_name, timeout)

    def cordon_node(self, node_name):
        return self.host.cordon_node(node_name)

    def uncordon_node(self, node_name):
        return self.host.uncordon_node(node_name)

    def drain_node(self, node_name, force, timeout):
        return self.host.drain_node(node_name, force, timeout)

    def add_node_label(self, node_name, key, value):
        return self.host.add_node_label(node_name, key, value)

    def remove_node_label(self, node_name, key):
        return self.host.remove_node_label(node_name, key)

    def get_node_capacity(self, node_name):
        return self.host.get_node_capacity(node_name)

    def get_node_vms(self, node_name):
        return self.host.get_node_vms(node_name)

    def cleanup(self):
        return self.host.cleanup()
