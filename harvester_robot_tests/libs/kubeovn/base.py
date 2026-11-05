"""
Kube-OVN Component: Base Class

Layer 4: Component and its implementation
"""

from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for kube-ovn (kubeovn-operator) implementations"""

    def __init__(self):
        self.unsupported_msg = f"Unsupported by {self.__class__.__name__}, falling back."

    @abstractmethod
    def get_configuration(self):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def set_ovn_central_nodes_label(self, label):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_bootstrap_configuration(self):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def list_nodes_matching_label(self, label):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_deployment(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_daemonset(self, name):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def list_pods(self, label_selector):
        raise NotImplementedError(self.unsupported_msg)

    @abstractmethod
    def get_raft_cluster_status(self, database):
        raise NotImplementedError(self.unsupported_msg)
