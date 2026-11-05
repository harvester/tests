"""
Kube-OVN Component

Layer 4: Component and its implementation
"""

from utility.utility import logging
from .base import Base
from .crd import CRD
from .rest import Rest


class KubeOVN(Base):
    def __init__(self):
        self.crd = CRD()
        self.rest = Rest()

    def _call(self, method, *args):
        try:
            return getattr(self.crd, method)(*args)
        except NotImplementedError as e:
            logging(e)
            return getattr(self.rest, method)(*args)

    def get_configuration(self):
        return self._call("get_configuration")

    def set_ovn_central_nodes_label(self, label):
        return self._call("set_ovn_central_nodes_label", label)

    def get_bootstrap_configuration(self):
        return self._call("get_bootstrap_configuration")

    def list_nodes_matching_label(self, label):
        return self._call("list_nodes_matching_label", label)

    def get_deployment(self, name):
        return self._call("get_deployment", name)

    def get_daemonset(self, name):
        return self._call("get_daemonset", name)

    def list_pods(self, label_selector):
        return self._call("list_pods", label_selector)

    def get_raft_cluster_status(self, database):
        return self._call("get_raft_cluster_status", database)
