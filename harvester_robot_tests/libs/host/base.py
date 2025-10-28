"""
Base class for Host operations (optional - for common patterns)
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for Host implementations"""

    @abstractmethod
    def list_nodes(self):
        """List all nodes"""
        pass

    @abstractmethod
    def get_node_count(self):
        """Get total number of nodes"""
        pass

    @abstractmethod
    def get_node(self, node_name):
        """Get node details"""
        pass

    @abstractmethod
    def get_node_status(self, node_name):
        """Get node status"""
        pass

    @abstractmethod
    def get_node_by_index(self, index):
        """Get node name by index"""
        pass

    @abstractmethod
    def get_worker_nodes(self):
        """Get all worker nodes"""
        pass

    @abstractmethod
    def get_control_plane_nodes(self):
        """Get all control-plane nodes"""
        pass

    @abstractmethod
    def is_node_ready(self, node_name):
        """Check if a node is ready"""
        pass

    @abstractmethod
    def wait_for_node_ready(self, node_name, timeout):
        """Wait for a node to become ready"""
        pass

    @abstractmethod
    def cordon_node(self, node_name):
        """Cordon a node"""
        pass

    @abstractmethod
    def uncordon_node(self, node_name):
        """Uncordon a node"""
        pass

    @abstractmethod
    def drain_node(self, node_name, force, timeout):
        """Drain a node"""
        pass

    @abstractmethod
    def add_node_label(self, node_name, key, value):
        """Add a label to a node"""
        pass

    @abstractmethod
    def remove_node_label(self, node_name, key):
        """Remove a label from a node"""
        pass
