"""
Host Rest Implementation - makes actual API calls using get_harvester_api_client()
"""
import time
from datetime import datetime, timedelta
from utility.utility import get_harvester_api_client
from utility.utility import logging
from host.base import Base


class Rest(Base):
    """Host Rest implementation - makes actual API calls"""

    def __init__(self):
        pass

    def list_nodes(self):
        """List all nodes"""
        api = get_harvester_api_client()

        code, data = api.hosts.list()
        assert code == 200, f"Failed to list nodes: {code}, {data}"

        nodes = []
        for item in data.get('items', []):
            nodes.append({
                'name': item['metadata']['name'],
                'labels': item['metadata'].get('labels', {}),
                'creation_time': item['metadata']['creationTimestamp'],
                'status': item.get('status', {})
            })

        return nodes

    def get_node_count(self):
        """Get total number of nodes"""
        api = get_harvester_api_client()

        code, data = api.hosts.list()
        assert code == 200, f"Failed to get node count: {code}, {data}"

        count = len(data.get('items', []))
        logging(f"Total nodes in cluster: {count}")
        return count

    def get_node(self, node_name):
        """Get node details"""
        api = get_harvester_api_client()

        code, data = api.hosts.get(node_name)
        assert code == 200, f"Failed to get node {node_name}: {code}, {data}"

        return {
            'name': data['metadata']['name'],
            'labels': data['metadata'].get('labels', {}),
            'creation_time': data['metadata']['creationTimestamp'],
            'status': data.get('status', {})
        }

    def get_node_by_index(self, index):
        """Get node by index"""
        nodes = self.list_nodes()
        if index >= len(nodes):
            raise ValueError(f"Node index {index} out of range")
        return nodes[index]['name']

    def get_worker_nodes(self):
        """Get all worker nodes"""
        nodes = self.list_nodes()
        worker_nodes = []
        for node in nodes:
            labels = node['labels']
            if 'node-role.kubernetes.io/control-plane' not in labels and \
               'node-role.kubernetes.io/master' not in labels:
                worker_nodes.append(node['name'])
        return worker_nodes

    def get_control_plane_nodes(self):
        """Get all control-plane nodes"""
        nodes = self.list_nodes()
        control_nodes = []
        for node in nodes:
            labels = node['labels']
            if 'node-role.kubernetes.io/control-plane' in labels or \
               'node-role.kubernetes.io/master' in labels:
                control_nodes.append(node['name'])
        return control_nodes

    def get_node_status(self, node_name):
        """Get node status"""
        node = self.get_node(node_name)
        status = node['status']

        conditions = status.get('conditions', [])
        ready_condition = None
        for condition in conditions:
            if condition.get('type') == 'Ready':
                ready_condition = condition
                break

        return {
            'ready': ready_condition.get('status') == 'True' if ready_condition else False,
            'conditions': conditions,
            'capacity': status.get('capacity', {}),
            'allocatable': status.get('allocatable', {})
        }

    def is_node_ready(self, node_name):
        """Check if node is ready"""
        status = self.get_node_status(node_name)
        return status['ready']

    def wait_for_node_ready(self, node_name, timeout):
        """Wait for node to be ready"""
        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            if self.is_node_ready(node_name):
                return True
            time.sleep(5)

        raise AssertionError(f"Node {node_name} did not become ready within {timeout}s")

    def cordon_node(self, node_name):
        """Cordon a node"""
        api = get_harvester_api_client()
        code, data = api.hosts.cordon(node_name)
        assert code == 200, f"Failed to cordon node: {code}, {data}"

    def uncordon_node(self, node_name):
        """Uncordon a node"""
        api = get_harvester_api_client()
        code, data = api.hosts.uncordon(node_name)
        assert code == 200, f"Failed to uncordon node: {code}, {data}"

    def drain_node(self, node_name, force, timeout):
        """Drain a node"""
        api = get_harvester_api_client()
        code, data = api.hosts.drain(node_name, force=force, timeout=timeout)
        assert code == 200, f"Failed to drain node: {code}, {data}"

    def add_node_label(self, node_name, key, value):
        """Add label to node"""
        api = get_harvester_api_client()
        code, data = api.hosts.add_label(node_name, key, value)
        assert code == 200, f"Failed to add label: {code}, {data}"

    def remove_node_label(self, node_name, key):
        """Remove label from node"""
        api = get_harvester_api_client()
        code, data = api.hosts.remove_label(node_name, key)
        assert code == 200, f"Failed to remove label: {code}, {data}"

    def get_node_capacity(self, node_name):
        """Get node capacity"""
        status = self.get_node_status(node_name)
        return {
            'capacity': status['capacity'],
            'allocatable': status['allocatable']
        }

    def get_node_vms(self, node_name):
        """Get VMs on node"""
        api = get_harvester_api_client()
        code, data = api.vms.list()
        assert code == 200, f"Failed to list VMs: {code}, {data}"

        node_vms = []
        for vm in data.get('items', []):
            vm_node = vm.get('status', {}).get('nodeName')
            if vm_node == node_name:
                node_vms.append(vm['metadata']['name'])

        return node_vms

    def cleanup(self):
        """Clean up host test artifacts"""
        logging('Cleaning up host test artifacts')
