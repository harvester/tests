""" Kube-OVN Keyword Wrapper

Layer 3: Keyword wrapper (NO direct API calls)

Placement checks for the ovn-central NB/SB raft members rendered by the
kubeovn-operator (harvester/harvester#12133, harvester/kubeovn-operator#93).
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa E402
from kubeovn import KubeOVN  # noqa E402
from utility.utility import logging, get_retry_count_and_interval  # noqa E402

CONTROL_PLANE_LABEL = "node-role.kubernetes.io/control-plane=true"
ETCD_LABEL = "node-role.kubernetes.io/etcd=true"
RAFT_SERVER_RE = re.compile(r"\(\w+ at (?:tcp|ssl):\[?([0-9a-fA-F.:]+?)\]?:\d+\)")


def _container_env(workload, container):
    for c in workload["spec"]["template"]["spec"]["containers"]:
        if c["name"] == container:
            return {e["name"]: e.get("value") for e in (c.get("env") or [])}
    raise AssertionError(f"Container {container} not found")


def _ip_set(value):
    return sorted(ip.strip() for ip in (value or "").split(",") if ip.strip())


class kubeovn_keywords:
    """Kube-OVN keyword wrapper - creates the KubeOVN component and delegates"""

    def __init__(self):
        self._kubeovn = None

    @property
    def kubeovn(self):
        """Lazy initialize to allow API client setup first"""
        if self._kubeovn is None:
            self._kubeovn = KubeOVN()
        return self._kubeovn

    # ---- Configuration ----

    def configuration_exists(self):
        return self.kubeovn.get_configuration() is not None

    def get_master_nodes_label(self):
        return self.kubeovn.get_configuration()["spec"].get("masterNodesLabel", "")

    def get_ovn_central_nodes_label(self):
        spec = self.kubeovn.get_configuration()["spec"]
        return spec.get("ovnCentral", {}).get("nodesLabel", "")

    def set_ovn_central_nodes_label(self, label):
        self.kubeovn.set_ovn_central_nodes_label(label)

    def ovn_central_nodes_label_should_be(self, expected):
        actual = self.get_ovn_central_nodes_label()
        assert actual == expected, (
            f"Configuration spec.ovnCentral.nodesLabel is '{actual}', expected "
            f"'{expected}'. An operator/CRD without the field prunes it on "
            "admission (harvester/kubeovn-operator#93 not deployed)")

    def get_bootstrap_ovn_central(self):
        spec = self.kubeovn.get_bootstrap_configuration()
        assert spec is not None, "kubeovn bootstrap ConfigMap not found"
        return spec.get("ovnCentral") or {}

    # ---- Nodes ----

    def get_node_ips_matching_label(self, label):
        return sorted(n["ip"] for n in self.kubeovn.list_nodes_matching_label(label))

    def get_node_names_matching_label(self, label):
        return sorted(n["name"] for n in self.kubeovn.list_nodes_matching_label(label))

    def get_witness_node_names(self):
        """Nodes in the etcd quorum that are not control-plane nodes."""
        etcd = set(self.get_node_names_matching_label(ETCD_LABEL))
        control_plane = set(self.get_node_names_matching_label(CONTROL_PLANE_LABEL))
        return sorted(etcd - control_plane)

    def get_taints_of_nodes_matching_label(self, label):
        return {n["name"]: n["taints"]
                for n in self.kubeovn.list_nodes_matching_label(label)}

    # ---- Status ----

    def wait_for_ovn_central_node_addresses(self, expected_ips, field="ovnCentralNodeAddresses"):
        """Wait until status.<field> lists exactly expected_ips."""
        expected = sorted(expected_ips)
        retry_count, retry_interval = get_retry_count_and_interval()
        actual = None
        for _ in range(retry_count):
            status = self.kubeovn.get_configuration().get("status") or {}
            actual = sorted(status.get(field) or [])
            if actual == expected:
                return actual
            time.sleep(retry_interval)
        raise AssertionError(
            f"Configuration status.{field} is {actual}, expected {expected}")

    # ---- Rendered workloads ----

    def ovn_central_should_target_nodes(self, label, expected_ips):
        """Assert the ovn-central Deployment renders one replica per member,
        a required node affinity built from label, and NODE_IPS listing every
        member. Retries while the operator re-renders."""
        expected = sorted(expected_ips)
        parts = label.split("=", 1)
        key, value = parts[0], (parts[1] if len(parts) > 1 else None)
        retry_count, retry_interval = get_retry_count_and_interval()
        problems = []
        for _ in range(retry_count):
            problems = []
            deploy = self.kubeovn.get_deployment("ovn-central")
            replicas = deploy["spec"]["replicas"]
            if replicas != len(expected):
                problems.append(f"replicas={replicas}, expected {len(expected)}")
            node_ips = _ip_set(_container_env(deploy, "ovn-central").get("NODE_IPS"))
            if node_ips != expected:
                problems.append(f"NODE_IPS={node_ips}, expected {expected}")
            affinity = (deploy["spec"]["template"]["spec"].get("affinity") or {})
            required = ((affinity.get("node_affinity") or {})
                        .get("required_during_scheduling_ignored_during_execution") or {})
            exprs = [e for t in (required.get("node_selector_terms") or [])
                     for e in (t.get("match_expressions") or [])]
            if value is None:
                want = {"key": key, "operator": "Exists", "values": None}
            else:
                want = {"key": key, "operator": "In", "values": [value]}
            if not any(e["key"] == want["key"] and e["operator"] == want["operator"]
                       and (e.get("values") or None) == want["values"] for e in exprs):
                problems.append(f"node affinity {exprs} does not select {label}")
            if not problems:
                return
            time.sleep(retry_interval)
        raise AssertionError("ovn-central Deployment does not follow "
                             f"{label}: {'; '.join(problems)}")

    def ovn_db_ips_should_be(self, kind, name, container, expected_ips):
        """Assert OVN_DB_IPS of a Deployment/DaemonSet lists expected_ips."""
        expected = sorted(expected_ips)
        getter = (self.kubeovn.get_deployment if kind.lower() == "deployment"
                  else self.kubeovn.get_daemonset)
        retry_count, retry_interval = get_retry_count_and_interval()
        actual = None
        for _ in range(retry_count):
            actual = _ip_set(_container_env(getter(name), container).get("OVN_DB_IPS"))
            if actual == expected:
                return
            time.sleep(retry_interval)
        raise AssertionError(f"{kind} {name} OVN_DB_IPS={actual}, expected {expected}")

    def deployment_replicas_should_be(self, name, expected):
        replicas = self.kubeovn.get_deployment(name)["spec"]["replicas"]
        assert replicas == int(expected), (
            f"Deployment {name} has {replicas} replicas, expected {expected}")

    def pods_should_run_only_on_nodes(self, label_selector, node_names):
        """Wait until there is exactly one Running pod per node in node_names,
        no pod elsewhere and none Pending."""
        expected = sorted(node_names)
        retry_count, retry_interval = get_retry_count_and_interval()
        pods = []
        for _ in range(retry_count):
            pods = [p for p in self.kubeovn.list_pods(label_selector) if not p["deleting"]]
            running = sorted(p["node"] for p in pods if p["phase"] == "Running")
            if running == expected and len(pods) == len(expected):
                return
            time.sleep(retry_interval)
        raise AssertionError(
            f"Pods {label_selector}: {pods}, expected one Running pod on each of {expected}")

    def no_pod_should_run_on_nodes(self, label_selector, node_names):
        pods = self.kubeovn.list_pods(label_selector)
        offenders = [p for p in pods if p["node"] in node_names]
        assert not offenders, f"Pods {label_selector} found on {node_names}: {offenders}"

    # ---- Raft ----

    def raft_members_should_be(self, database, expected_ips):
        """Wait until the NB or SB raft lists exactly expected_ips as servers
        and has an elected leader."""
        expected = sorted(expected_ips)
        retry_count, retry_interval = get_retry_count_and_interval()
        output = ""
        for _ in range(retry_count):
            try:
                output = self.kubeovn.get_raft_cluster_status(database)
            except Exception as e:  # pod may be rolling
                logging(f"cluster/status {database} not available yet: {e}")
                time.sleep(retry_interval)
                continue
            servers_block = output.split("Servers:", 1)[-1] if "Servers:" in output else ""
            members = sorted(RAFT_SERVER_RE.findall(servers_block))
            leader = re.search(r"^Leader:\s*(\S+)", output, re.MULTILINE)
            if members == expected and leader and leader.group(1) != "unknown":
                logging(f"{database} raft members {members}, leader {leader.group(1)}")
                return members
            time.sleep(retry_interval)
        raise AssertionError(
            f"{database} raft does not have members {expected} with a leader:\n{output}")

    def bootstrap_ovn_central_should_tolerate_witness_taint(self):
        """The bootstrap ovnCentral tolerations must cover the witness taint
        node-role.kubernetes.io/etcd=true:NoExecute."""
        tolerations = self.get_bootstrap_ovn_central().get("tolerations") or []
        for t in tolerations:
            effect_ok = t.get("effect") in (None, "", "NoExecute")
            if t.get("operator") == "Exists" and effect_ok and \
                    t.get("key") in (None, "", "node-role.kubernetes.io/etcd"):
                return
            if t.get("key") == "node-role.kubernetes.io/etcd" and \
                    t.get("value") == "true" and effect_ok:
                return
        raise AssertionError(
            "Bootstrap ovnCentral tolerations do not cover the witness taint "
            f"node-role.kubernetes.io/etcd=true:NoExecute: {tolerations}")
