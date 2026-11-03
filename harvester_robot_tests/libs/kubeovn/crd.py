"""
Kube-OVN Component: CRD Implementation

Layer 4: Component and its implementation

Reads and patches the kubeovn-operator Configuration (kubeovn.io/v1) and
inspects the workloads the operator renders from it (ovn-central,
kube-ovn-controller, ovs-ovn) through the Kubernetes API.
"""

import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from crd import get_cr, patch_cr
from utility.utility import logging
from .base import Base

KUBEOVN_GROUP = "kubeovn.io"
KUBEOVN_VERSION = "v1"
KUBEOVN_NAMESPACE = "kube-system"
CONFIGURATION_PLURAL = "configurations"
CONFIGURATION_NAME = "kubeovn"
BOOTSTRAP_CONFIGMAP = "kubeovn-configuration-bootstrap"
BOOTSTRAP_KEY = "configuration.yaml"

# OVSDB control sockets inside the ovn-central container
RAFT_CTL = {
    "OVN_Northbound": "/var/run/ovn/ovnnb_db.ctl",
    "OVN_Southbound": "/var/run/ovn/ovnsb_db.ctl",
}


def label_to_selector(label):
    """Turn a kubeovn-operator node label ("key=value" or "key") into a
    Kubernetes label selector, which already uses the same syntax."""
    return label.strip()


class CRD(Base):
    """CRD implementation for kube-ovn operations using the Kubernetes API"""

    def __init__(self):
        super().__init__()
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()
        self.common_parameters = {
            "group": KUBEOVN_GROUP,
            "version": KUBEOVN_VERSION,
            "namespace": KUBEOVN_NAMESPACE,
            "plural": CONFIGURATION_PLURAL,
        }

    def get_configuration(self):
        try:
            return get_cr(**self.common_parameters, name=CONFIGURATION_NAME)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def set_ovn_central_nodes_label(self, label):
        """Set spec.ovnCentral.nodesLabel; an empty label removes the field.

        A merge patch is used so only this field changes. Operators without
        the field in their CRD schema prune it on admission, which leaves the
        Configuration unchanged.
        """
        value = label if label else None
        body = {"spec": {"ovnCentral": {"nodesLabel": value}}}
        logging(f"Patching Configuration {CONFIGURATION_NAME}: "
                f"spec.ovnCentral.nodesLabel={value}")
        return patch_cr(**self.common_parameters, name=CONFIGURATION_NAME,
                        body=body)

    def get_bootstrap_configuration(self):
        """Return the parsed Configuration spec the operator bootstraps from,
        or None when the ConfigMap does not exist."""
        try:
            cm = self.core_api.read_namespaced_config_map(
                name=BOOTSTRAP_CONFIGMAP, namespace=KUBEOVN_NAMESPACE)
        except ApiException as e:
            if e.status == 404:
                return None
            raise
        return yaml.safe_load((cm.data or {}).get(BOOTSTRAP_KEY) or "{}")

    def list_nodes_matching_label(self, label):
        """Return [{name, ip, taints}] for nodes matching label."""
        nodes = self.core_api.list_node(
            label_selector=label_to_selector(label)).items
        result = []
        for node in nodes:
            ip = next((a.address for a in (node.status.addresses or [])
                       if a.type == "InternalIP"), None)
            taints = [f"{t.key}={t.value or ''}:{t.effect}"
                      for t in (node.spec.taints or [])]
            result.append({"name": node.metadata.name, "ip": ip,
                           "taints": taints})
        return result

    def get_deployment(self, name):
        return self.apps_api.read_namespaced_deployment(
            name=name, namespace=KUBEOVN_NAMESPACE).to_dict()

    def get_daemonset(self, name):
        return self.apps_api.read_namespaced_daemon_set(
            name=name, namespace=KUBEOVN_NAMESPACE).to_dict()

    def list_pods(self, label_selector):
        pods = self.core_api.list_namespaced_pod(
            namespace=KUBEOVN_NAMESPACE, label_selector=label_selector).items
        return [{"name": p.metadata.name,
                 "node": p.spec.node_name,
                 "phase": p.status.phase,
                 "deleting": p.metadata.deletion_timestamp is not None}
                for p in pods]

    def get_raft_cluster_status(self, database):
        """Run `cluster/status <database>` in a Running ovn-central pod and
        return the raw output."""
        ctl = RAFT_CTL[database]
        pods = [p for p in self.list_pods("app=ovn-central")
                if p["phase"] == "Running" and not p["deleting"]]
        assert pods, "No Running ovn-central pod to query the raft status"
        return stream(
            self.core_api.connect_get_namespaced_pod_exec,
            pods[0]["name"], KUBEOVN_NAMESPACE, container="ovn-central",
            command=["ovn-appctl", "-t", ctl, "cluster/status", database],
            stderr=True, stdin=False, stdout=True, tty=False)
