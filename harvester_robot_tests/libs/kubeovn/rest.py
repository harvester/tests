"""
Kube-OVN Component: REST Implementation

Layer 4: Component and its implementation

The kubeovn-operator Configuration and the kube-ovn workloads are not exposed
through the Harvester REST API, so every method falls back to the CRD
strategy.
"""

from .base import Base


class Rest(Base):
    """REST implementation for kube-ovn operations"""

    def __init__(self):
        super().__init__()

    def get_configuration(self):
        return super().get_configuration()

    def set_ovn_central_nodes_label(self, label):
        return super().set_ovn_central_nodes_label(label)

    def get_bootstrap_configuration(self):
        return super().get_bootstrap_configuration()

    def list_nodes_matching_label(self, label):
        return super().list_nodes_matching_label(label)

    def get_deployment(self, name):
        return super().get_deployment(name)

    def get_daemonset(self, name):
        return super().get_daemonset(name)

    def list_pods(self, label_selector):
        return super().list_pods(label_selector)

    def get_raft_cluster_status(self, database):
        return super().get_raft_cluster_status(database)
