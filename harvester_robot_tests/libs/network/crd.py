"""
Network CRD Implementation - Kubernetes API operations
Layer 4: Makes actual kubectl/K8s API calls for network operations
"""

import time
import json
from kubernetes import client
from kubernetes.client.rest import ApiException
from constant import DEFAULT_NAMESPACE
from utility.utility import logging
from network.base import Base


class CRD(Base):
    """
    CRD implementation for Network operations using Kubernetes API
    """

    def __init__(self):
        """Initialize Kubernetes clients"""
        self.custom_api = client.CustomObjectsApi()

    # Cluster Network Operations
    def create_cluster_network(self, name):
        """Create cluster network"""
        logging(f"Creating cluster network: {name}")

        spec = {
            "apiVersion": "network.harvesterhci.io/v1beta1",
            "kind": "ClusterNetwork",
            "metadata": {
                "name": name
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="clusternetworks",
                body=spec
            )
            logging(f"Created cluster network: {name}")
            return spec
        except ApiException as e:
            if e.status == 409:
                logging(f"Cluster network {name} already exists")
                return spec
            raise Exception(
                f"Failed to create cluster network: {e}"
            )

    def delete_cluster_network(self, name):
        """Delete cluster network"""
        logging(f"Deleting cluster network: {name}")
        try:
            self.custom_api.delete_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="clusternetworks",
                name=name
            )
            logging(f"Deleted cluster network: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(
                    f"Failed to delete cluster network: {e}"
                )

    def create_vlan_config(self, name, cluster_network, nic):
        """Create VLAN config to bind NIC to cluster network"""
        logging(f"Creating VLAN config: {name} "
                f"(nic={nic}, cluster_network={cluster_network})")

        spec = {
            "apiVersion": "network.harvesterhci.io/v1beta1",
            "kind": "VlanConfig",
            "metadata": {
                "name": name,
                "labels": {
                    "network.harvesterhci.io/clusternetwork":
                        cluster_network
                }
            },
            "spec": {
                "clusterNetwork": cluster_network,
                "uplink": {
                    "bondOptions": {
                        "miimon": -1,
                        "mode": "active-backup"
                    },
                    "linkAttributes": {
                        "txQLen": -1
                    },
                    "nics": [nic]
                }
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="vlanconfigs",
                body=spec
            )
            logging(f"Created VLAN config: {name}")
            return spec
        except ApiException as e:
            if e.status == 409:
                logging(f"VLAN config {name} already exists")
                return spec
            raise Exception(
                f"Failed to create VLAN config: {e}"
            )

    def delete_vlan_config(self, name):
        """Delete VLAN config"""
        logging(f"Deleting VLAN config: {name}")
        try:
            self.custom_api.delete_cluster_custom_object(
                group="network.harvesterhci.io",
                version="v1beta1",
                plural="vlanconfigs",
                name=name
            )
            logging(f"Deleted VLAN config: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(
                    f"Failed to delete VLAN config: {e}"
                )

    def wait_for_cluster_network_ready(self, name, timeout=120):
        """Wait for cluster network to become ready"""
        logging(f"Waiting for cluster network {name} to be ready")
        deadline = time.time() + int(timeout)

        while time.time() < deadline:
            try:
                cn = self.custom_api.get_cluster_custom_object(
                    group="network.harvesterhci.io",
                    version="v1beta1",
                    plural="clusternetworks",
                    name=name
                )
                conditions = cn.get("status", {}).get(
                    "conditions", []
                )
                for cond in conditions:
                    if (cond.get("type") == "ready"
                            and cond.get("status") == "True"):
                        logging(
                            f"Cluster network {name} is ready"
                        )
                        return cn
            except ApiException:
                pass
            time.sleep(5)

        raise Exception(
            f"Cluster network {name} not ready within {timeout}s"
        )

    # VLAN Network Operations
    def create_vlan_network(self, name, vlan_id, cluster_network):
        """Create VLAN network"""
        logging(f"Creating VLAN network: {name}")

        network_spec = {
            "apiVersion": "k8s.cni.cncf.io/v1",
            "kind": "NetworkAttachmentDefinition",
            "metadata": {
                "name": name,
                "namespace": DEFAULT_NAMESPACE,
                "annotations": {
                    "network.harvesterhci.io/route":
                        '{"mode":"auto"}'
                },
                "labels": {
                    "network.harvesterhci.io/clusternetwork":
                        cluster_network,
                    "network.harvesterhci.io/type": "L2VlanNetwork"
                }
            },
            "spec": {
                "config": json.dumps({
                    "cniVersion": "0.3.1",
                    "name": name,
                    "type": "bridge",
                    "bridge": f"{cluster_network}-br",
                    "promiscMode": True,
                    "vlan": int(vlan_id),
                    "ipam": {}
                })
            }
        }

        try:
            self.custom_api.create_namespaced_custom_object(
                group="k8s.cni.cncf.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="network-attachment-definitions",
                body=network_spec
            )
            logging(f"Created VLAN network: {name}")
            return network_spec
        except ApiException as e:
            if e.status == 409:
                logging(f"VLAN network {name} already exists")
                return network_spec
            raise Exception(
                f"Failed to create VLAN network: {e}"
            )

    def delete_vlan_network(self, name):
        """Delete VLAN network"""
        logging(f"Deleting VLAN network: {name}")
        try:
            self.custom_api.delete_namespaced_custom_object(
                group="k8s.cni.cncf.io",
                version="v1",
                namespace=DEFAULT_NAMESPACE,
                plural="network-attachment-definitions",
                name=name
            )
            logging(f"Deleted VLAN network: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(
                    f"Failed to delete VLAN network: {e}"
                )

    # IP Pool Operations
    def get_ip_pool(self, name):
        """Get IP pool by name, returns None if not found"""
        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"
        try:
            return self.custom_api.get_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            raise Exception(f"Failed to get IP pool: {e}")

    def create_ip_pool(self, name, subnet, start_ip, end_ip, network_id):
        """Create IP pool, reusing existing pool with the same name"""
        logging(f"Creating IP pool: {name}")

        existing = self.get_ip_pool(name)
        if existing:
            logging(f"IP pool {name} already exists, reusing")
            return existing

        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"

        ippool_spec = {
            "apiVersion": f"{lb_group}/{lb_version}",
            "kind": "IPPool",
            "metadata": {
                "name": name
            },
            "spec": {
                "ranges": [{
                    "subnet": subnet,
                    "rangeStart": start_ip,
                    "rangeEnd": end_ip,
                    "gateway": "",
                    "type": "range" if start_ip or end_ip
                    else "cidr"
                }],
                "selector": {
                    "network": network_id,
                    "scope": [{
                        "namespace": "*",
                        "project": "*",
                        "guestCluster": "*"
                    }]
                }
            }
        }

        try:
            self.custom_api.create_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                body=ippool_spec
            )
            logging(f"Created IP pool: {name}")
            return ippool_spec
        except ApiException as e:
            if e.status == 409:
                logging(f"IP pool {name} already exists")
                return ippool_spec
            raise Exception(
                f"Failed to create IP pool: {e}"
            )

    def delete_ip_pool(self, name):
        """Delete IP pool"""
        logging(f"Deleting IP pool: {name}")

        lb_group = "loadbalancer.harvesterhci.io"
        lb_version = "v1beta1"

        try:
            self.custom_api.delete_cluster_custom_object(
                group=lb_group,
                version=lb_version,
                plural="ippools",
                name=name
            )
            logging(f"Deleted IP pool: {name}")
        except ApiException as e:
            if e.status != 404:
                raise Exception(
                    f"Failed to delete IP pool: {e}"
                )
