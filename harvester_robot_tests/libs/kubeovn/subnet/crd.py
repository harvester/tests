"""
KubeOVN Subnet CRD implementation
"""


from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import create_cluster_cr, delete_cluster_cr, get_cluster_cr
from constant import (
    KUBEOVN_API_GROUP,
    KUBEOVN_API_VERSION,
    KUBEOVN_SUBNET_PLURAL,
)
from utility.utility import logging
from subnet.base import Base


class CRD(Base):
    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.group = KUBEOVN_API_GROUP
        self.version = KUBEOVN_API_VERSION
        self.plural = KUBEOVN_SUBNET_PLURAL

    def create_subnet(self, name, **kwargs):
        """
        Create new KubeOVN Subnet

        Args:
            name: Name of new KubeOVN Subnet
            **kwargs: Additional parameters as keyword arguments

        Returns:
            dict: KubeOVN Subnet Object
        """
        try:
            default = kwargs.get("default", False)
            vpc = kwargs.get("vpc", "ovn-cluster")
            cidr_block = kwargs.get("cidr_block", "")
            provider = kwargs.get("provider", "ovn")

            body = {
                "apiVersion": f"{self.group}/{self.version}",
                "kind": "Subnet",
                "metadata": {
                    "name": name,
                    "labels": {
                        "harvesterhci.io/creator": "robot-framework",
                    },
                },
                "spec": {
                    "default": default,
                    "vpc": vpc,
                    "cidrBlock": cidr_block,
                    "provider": provider,
                },
            }

            subnet = create_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                body=body
            )
            logging(f"Created KubeOVN Subnet {name}")
            return subnet
        except ApiException as err:
            raise Exception(f"Failed to create KubeOVN Subnet {name}: {err}") from err

    def get(self, name):
        try:
            subnet = get_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=name
            )
            logging(f"Retrieved KubeOVN Subnet {name}")
            return subnet
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN Subnet {name} does not exist")
                return None
            raise Exception(f"Failed to get KubeOVN Subnet {name}: {err}") from err

    def delete(self, name):
        try:
            subnet = delete_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=name
            )
            logging(f"Deleted KubeOVN Subnet {name}")
            return subnet
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN Subnet {name} does not exist")
                return None
            raise Exception(f"Failed to delete KubeOVN Subnet {name}: {err}") from err
