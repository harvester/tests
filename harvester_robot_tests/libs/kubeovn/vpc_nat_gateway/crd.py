"""
KubeOVN VPC CRD implementation
"""
import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cluster_cr, create_cluster_cr, delete_cluster_cr, list_cluster_cr
from constant import (
    DEFAULT_TIMEOUT,
    KUBE_SYSTEM_NAMESPACE,
    KUBEOVN_API_GROUP,
    KUBEOVN_API_VERSION,
    KUBEOVN_SUBNET_PLURAL,
    KUBEOVN_VPC_NAT_GATEWAY_PLURAL,
)
from utility.utility import logging
from vpc_nat_gateway.base import Base


class CRD(Base):
    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.group = KUBEOVN_API_GROUP
        self.version = KUBEOVN_API_VERSION
        self.plural = KUBEOVN_VPC_NAT_GATEWAY_PLURAL

    def get_all(self):
        try:
            gateways = list_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
            )
            logging("Retrieved all KubeOVN VPC NAT Gateways")
            return gateways
        except ApiException as err:
            raise Exception(f"{err}") from err

    def get(self, name):
        """
        Get KubeOVN VPC NAT Gateway details

        Args:
            name: Name of the KubeOVN VPC NAT Gateway

        Returns:
            dict: KubeOVN VPC NAT Gateway object
        """
        try:
            gateway = get_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=name
            )
            logging(f"Retrieved KubeOVN VPC NAT Gateway {name}")
            return gateway
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN VPC NAT Gateway {name} does not exist")
                return None
            raise Exception(f"Failed to get KubeOVN VPC NAT Gateway {name}: {err}") from err

    def create(self, name, **kwargs):
        try:
            vpc = kwargs.get("vpc", None)
            lan_ip = kwargs.get("lan_ip", None)
            internal_subnet = kwargs.get("internal_subnet", None)
            external_subnets = kwargs.get("external_subnets", [])
            timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

            internal_subnet_cr = get_cluster_cr(
                group=KUBEOVN_API_GROUP,
                version=KUBEOVN_API_VERSION,
                plural=KUBEOVN_SUBNET_PLURAL,
                name=internal_subnet
            )
            provider_split = internal_subnet_cr.get("spec", {}).get("provider", "ovn").split(".")
            if len(provider_split) >= 2:
                internal_network = provider_split[0]
                namespace = provider_split[1]

            body = {
                "apiVersion": f"{self.group}/{self.version}",
                "kind": "VpcNatGateway",
                "metadata": {
                    "name": name,
                    "annotations": {
                        "k8s.v1.cni.cncf.io/networks": f"{namespace}/{internal_network}",
                    },
                    "labels": {
                        "harvesterhci.io/creator": "robot-framework",
                    },
                },
                "spec": {
                    "vpc": vpc,
                    "subnet": internal_subnet,
                    "lanIp": lan_ip,
                    "externalSubnets": external_subnets,
                },
            }

            gateway = create_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                body=body
            )
            logging(f"Created KubeOVN VPC NAT Gateway {name}")

            endtime = time.time() + timeout
            while time.time() < endtime:
                pods = self.core_api.list_namespaced_pod(
                        KUBE_SYSTEM_NAMESPACE,
                        label_selector=f"app=vpc-nat-gw-{name}"
                )
                for pod in pods.items:
                    if pod.status.phase == "Running":
                        return gateway
                time.sleep(15)

            raise TimeoutError(f"VPC NAT Gateway Pod for {name} not ready in time")
        except ApiException as err:
            raise Exception(f"Failed to create KubeOVN VPC NAT Gateway {name}: {err}") from err

    def delete(self, name, **kwargs):
        try:
            timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

            gateway = delete_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=name
            )

            endtime = time.time() + timeout
            while time.time() < endtime:
                time.sleep(15)

                # wait until all gateway pods are gone
                pods = self.core_api.list_namespaced_pod(
                        KUBE_SYSTEM_NAMESPACE,
                        label_selector=f"app=vpc-nat-gw-{name}"
                )
                if len(pods) > 0:
                    continue

                # then continue to wait until there are no more IPs in use
                for external_subnet in gateway["spec"]["externalSubnets"]:
                    subnet = get_cluster_cr(
                        group=self.group,
                        version=self.version,
                        plural=KUBEOVN_SUBNET_PLURAL,
                        name=external_subnet
                    )
                    if subnet.status.v4usingIPs == 0:
                        continue

                logging(f"Deleted KubeOVN VPC NAT Gateway {name}")
                return gateway

            raise TimeoutError(f"VPC NAT Gateway Pod for {name} not deleted in time")
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN VPC {name} already deleted")
                return None
            raise Exception(f"Failed to delete KubeOVN VPC NAT Gateway {name}: {err}") from err

    def cleanup(self):
        try:
            gateways = list_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
            )

            for gateway in gateways:
                name = gateway.get("metadata", {}).get("name")
                delete_cluster_cr(
                    group=self.group,
                    version=self.version,
                    plural=self.plural,
                    name=name
                )
                logging(f"Deleted KubeOVN VPC NAT Gateway {name}")
        except ApiException as err:
            raise Exception(f"{err}") from err
