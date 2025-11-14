"""
Host CRD Implementation
Uses Kubernetes Node resources for host/node operations
"""
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from utility.utility import logging, get_retry_count_and_interval
from constant import DEFAULT_TIMEOUT_SHORT, DEFAULT_TIMEOUT
from host.base import Base


class CRD(Base):
    """
    Host CRD implementation
    Uses Kubernetes Node resources (not CRDs, but native K8s resources)
    """

    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def list_nodes(self):
        """List all nodes in the cluster"""
        try:
            nodes = self.core_api.list_node()

            result = []
            for node in nodes.items:
                result.append({
                    'name': node.metadata.name,
                    'labels': node.metadata.labels or {},
                    'annotations': node.metadata.annotations or {},
                    'creation_time': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else '',      # NOQA
                    'status': self._extract_node_status(node)
                })

            return result
        except ApiException as e:
            logging(f"Failed to list nodes: {e}")
            raise

    def get_node_count(self):
        """Get total number of nodes in the cluster"""
        try:
            nodes = self.core_api.list_node()
            count = len(nodes.items)
            logging(f"Total nodes in cluster: {count}")
            return count
        except ApiException as e:
            logging(f"Failed to get node count: {e}")
            raise

    def get_node(self, node_name):
        """Get specific node details"""
        try:
            node = self.core_api.read_node(name=node_name)

            return {
                'name': node.metadata.name,
                'labels': node.metadata.labels or {},
                'annotations': node.metadata.annotations or {},
                'creation_time': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else '',      # NOQA
                'status': self._extract_node_status(node)
            }
        except ApiException as e:
            logging(f"Failed to get node {node_name}: {e}")
            raise

    def get_node_by_index(self, index):
        """Get node name by index"""
        nodes = self.list_nodes()

        if index >= len(nodes):
            raise ValueError(f"Node index {index} out of range (total nodes: {len(nodes)})")

        return nodes[index]['name']

    def get_worker_nodes(self):
        """Get all worker node names"""
        nodes = self.list_nodes()

        worker_nodes = []
        for node in nodes:
            labels = node['labels']
            # Check if node is NOT a control-plane node
            is_control_plane = (
                'node-role.kubernetes.io/control-plane' in labels or
                'node-role.kubernetes.io/master' in labels
            )
            if not is_control_plane:
                worker_nodes.append(node['name'])

        return worker_nodes

    def get_control_plane_nodes(self):
        """Get all control-plane node names"""
        nodes = self.list_nodes()

        control_nodes = []
        for node in nodes:
            labels = node['labels']
            # Check if node is a control-plane node
            is_control_plane = (
                'node-role.kubernetes.io/control-plane' in labels or
                'node-role.kubernetes.io/master' in labels
            )
            if is_control_plane:
                control_nodes.append(node['name'])

        return control_nodes

    def get_node_status(self, node_name):
        """Get node status"""
        node_info = self.get_node(node_name)
        return node_info['status']

    def is_node_ready(self, node_name):
        """Check if node is in Ready state"""
        status = self.get_node_status(node_name)
        return status.get('ready', False)

    def wait_for_node_ready(self, node_name, timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait for node to become ready"""
        endtime = time.time() + timeout

        while time.time() < endtime:
            if self.is_node_ready(node_name):
                logging(f"Node {node_name} is ready")
                return True

            logging(f"Waiting for node {node_name} to be ready...")
            time.sleep(5)

        raise AssertionError(f"Node {node_name} did not become ready within {timeout}s")

    def cordon_node(self, node_name):
        """Cordon a node (mark as unschedulable)"""
        try:
            # Patch node to set spec.unschedulable=true
            body = {
                "spec": {
                    "unschedulable": True
                }
            }

            self.core_api.patch_node(name=node_name, body=body)
            logging(f"Node {node_name} cordoned successfully")
        except ApiException as e:
            logging(f"Failed to cordon node {node_name}: {e}")
            raise

    def uncordon_node(self, node_name):
        """Uncordon a node (mark as schedulable)"""
        try:
            # Patch node to set spec.unschedulable=false
            body = {
                "spec": {
                    "unschedulable": False
                }
            }

            self.core_api.patch_node(name=node_name, body=body)
            logging(f"Node {node_name} uncordoned successfully")
        except ApiException as e:
            logging(f"Failed to uncordon node {node_name}: {e}")
            raise

    def drain_node(self, node_name, force=False, timeout=DEFAULT_TIMEOUT):
        """
        Drain a node (evict all pods)
        Note: This requires kubectl drain or manual pod eviction
        """
        logging(f"Draining node {node_name}")

        # First cordon the node
        self.cordon_node(node_name)

        # Get all pods on the node
        try:
            pods = self.core_api.list_pod_for_all_namespaces(
                field_selector=f'spec.nodeName={node_name}'
            )

            # Evict each pod (except DaemonSet pods if force=False)
            for pod in pods.items:
                owner_refs = pod.metadata.owner_references or []
                is_daemonset = any(ref.kind == 'DaemonSet' for ref in owner_refs)

                if is_daemonset and not force:
                    logging(f"Skipping DaemonSet pod {pod.metadata.name}")
                    continue

                # Delete the pod
                try:
                    self.core_api.delete_namespaced_pod(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace
                    )
                    logging(f"Deleted pod {pod.metadata.namespace}/{pod.metadata.name}")
                except ApiException as e:
                    if e.status != 404:
                        logging(f"Error deleting pod: {e}")

            logging(f"Node {node_name} drained successfully")
        except ApiException as e:
            logging(f"Error during node drain: {e}")
            raise

    def add_node_label(self, node_name, key, value):
        """Add label to a node"""
        try:
            # Get current node
            node = self.core_api.read_node(name=node_name)

            # Add label
            if node.metadata.labels is None:
                node.metadata.labels = {}
            node.metadata.labels[key] = value

            # Patch node
            body = {
                "metadata": {
                    "labels": node.metadata.labels
                }
            }

            self.core_api.patch_node(name=node_name, body=body)
            logging(f"Added label {key}={value} to node {node_name}")
        except ApiException as e:
            logging(f"Failed to add label to node {node_name}: {e}")
            raise

    def remove_node_label(self, node_name, key):
        """Remove label from a node"""
        try:
            # Get current node
            node = self.core_api.read_node(name=node_name)

            # Remove label
            if node.metadata.labels and key in node.metadata.labels:
                del node.metadata.labels[key]

                # Patch node
                body = {
                    "metadata": {
                        "labels": node.metadata.labels
                    }
                }

                self.core_api.patch_node(name=node_name, body=body)
                logging(f"Removed label {key} from node {node_name}")
        except ApiException as e:
            logging(f"Failed to remove label from node {node_name}: {e}")
            raise

    def get_node_capacity(self, node_name):
        """Get node resource capacity"""
        try:
            node = self.core_api.read_node(name=node_name)

            capacity = node.status.capacity or {}
            allocatable = node.status.allocatable or {}

            return {
                'capacity': {
                    'cpu': capacity.get('cpu', '0'),
                    'memory': capacity.get('memory', '0'),
                    'storage': capacity.get('ephemeral-storage', '0'),
                    'pods': capacity.get('pods', '0')
                },
                'allocatable': {
                    'cpu': allocatable.get('cpu', '0'),
                    'memory': allocatable.get('memory', '0'),
                    'storage': allocatable.get('ephemeral-storage', '0'),
                    'pods': allocatable.get('pods', '0')
                }
            }
        except ApiException as e:
            logging(f"Failed to get node capacity: {e}")
            raise

    def get_node_vms(self, node_name):
        """
        Get all VMs running on a specific node
        Note: This requires querying VirtualMachine CRs
        """
        from crd import list_cr
        from constant import KUBEVIRT_API_GROUP, KUBEVIRT_API_VERSION, VIRTUALMACHINE_PLURAL

        try:
            # List all VMs
            vms = list_cr(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace='',  # All namespaces
                plural=VIRTUALMACHINE_PLURAL
            )

            node_vms = []
            for vm in vms.get('items', []):
                vm_node = vm.get('status', {}).get('nodeName')
                if vm_node == node_name:
                    node_vms.append({
                        'name': vm['metadata']['name'],
                        'namespace': vm['metadata']['namespace'],
                        'phase': vm.get('status', {}).get('phase', 'Unknown')
                    })

            return node_vms
        except Exception as e:
            logging(f"Failed to get VMs on node {node_name}: {e}")
            return []

    def cleanup(self):
        """Clean up host test artifacts"""
        logging('Cleaning up host test artifacts')
        # Could remove test labels, uncordon nodes, etc.

    def _extract_node_status(self, node):
        """Extract and format node status"""
        conditions = node.status.conditions or []

        # Find Ready condition
        ready_condition = None
        for condition in conditions:
            if condition.type == 'Ready':
                ready_condition = condition
                break

        return {
            'ready': ready_condition.status == 'True' if ready_condition else False,
            'ready_reason': ready_condition.reason if ready_condition else '',
            'ready_message': ready_condition.message if ready_condition else '',
            'conditions': [
                {
                    'type': c.type,
                    'status': c.status,
                    'reason': c.reason or '',
                    'message': c.message or ''
                }
                for c in conditions
            ],
            'addresses': [
                {'type': addr.type, 'address': addr.address}
                for addr in (node.status.addresses or [])
            ],
            'capacity': dict(node.status.capacity or {}),
            'allocatable': dict(node.status.allocatable or {}),
            'node_info': {
                'architecture': node.status.node_info.architecture if node.status.node_info else '',    # NOQA
                'kernel_version': node.status.node_info.kernel_version if node.status.node_info else '',    # NOQA
                'os_image': node.status.node_info.os_image if node.status.node_info else '',
                'container_runtime': node.status.node_info.container_runtime_version if node.status.node_info else ''   # NOQA
            }
        }
