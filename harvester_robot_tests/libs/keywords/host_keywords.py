
"""
Layer 3: Host Keywords - creates Host() instance and delegates - NO direct API calls!
"""

from utility.utility import logging
from host import Host
from constant import DEFAULT_TIMEOUT_SHORT, DEFAULT_TIMEOUT


class host_keywords:
    """Layer 3: Host keyword wrapper - creates Host component and delegates"""

    def __init__(self):
        self.host = Host()

    def cleanup_hosts(self):
        """Clean up all test hosts"""
        self.host.cleanup()

    def list_nodes(self):
        """List all nodes"""
        logging('Listing all nodes')
        return self.host.list_nodes()

    def get_node_count(self):
        """Get total number of nodes in the cluster"""
        logging('Getting node count')
        return self.host.get_node_count()

    def get_node(self, node_name):
        """Get node details"""
        logging(f'Getting node {node_name}')
        return self.host.get_node(node_name)

    def get_node_by_index(self, index):
        """Get node by index"""
        logging(f'Getting node at index {index}')
        return self.host.get_node_by_index(int(index))

    def get_worker_nodes(self):
        """Get all worker nodes"""
        logging('Getting worker nodes')
        return self.host.get_worker_nodes()

    def get_control_plane_nodes(self):
        """Get all control-plane nodes"""
        logging('Getting control-plane nodes')
        return self.host.get_control_plane_nodes()

    def get_node_status(self, node_name):
        """Get node status"""
        logging(f'Getting status for node {node_name}')
        return self.host.get_node_status(node_name)

    def is_node_ready(self, node_name):
        """Check if node is ready"""
        return self.host.is_node_ready(node_name)

    def wait_for_node_ready(self, node_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for node to be ready"""
        logging(f'Waiting for node {node_name} to be ready')
        self.host.wait_for_node_ready(node_name, timeout)

    def cordon_node(self, node_name):
        """Cordon a node"""
        logging(f'Cordoning node {node_name}')
        self.host.cordon_node(node_name)

    def uncordon_node(self, node_name):
        """Uncordon a node"""
        logging(f'Uncordoning node {node_name}')
        self.host.uncordon_node(node_name)

    def drain_node(self, node_name, force=False, timeout=DEFAULT_TIMEOUT):
        """Drain a node"""
        logging(f'Draining node {node_name}')
        self.host.drain_node(node_name, force, timeout)

    def add_node_label(self, node_name, key, value):
        """Add label to node"""
        logging(f'Adding label {key}={value} to node {node_name}')
        self.host.add_node_label(node_name, key, value)

    def remove_node_label(self, node_name, key):
        """Remove label from node"""
        logging(f'Removing label {key} from node {node_name}')
        self.host.remove_node_label(node_name, key)

    def get_node_capacity(self, node_name):
        """Get node capacity"""
        logging(f'Getting capacity for node {node_name}')
        return self.host.get_node_capacity(node_name)

    def get_node_vms(self, node_name):
        """Get VMs on node"""
        logging(f'Getting VMs on node {node_name}')
        return self.host.get_node_vms(node_name)
