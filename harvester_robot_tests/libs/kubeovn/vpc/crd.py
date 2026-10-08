"""
KubeOVN VPC CRD implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cluster_cr, create_cluster_cr, delete_cluster_cr
from constant import (
    KUBEOVN_API_GROUP,
    KUBEOVN_API_VERSION,
    KUBEOVN_VPC_PLURAL,
)
from utility.utility import logging
from vpc.base import Base


class CRD(Base):
    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.group = KUBEOVN_API_GROUP
        self.version = KUBEOVN_API_VERSION
        self.plural = KUBEOVN_VPC_PLURAL

    def get_vpc(self, vpc_name):
        """
        Get KubeOVN VPC details

        Args:
            vpc_name: Name of the KubeOVN VPC

        Returns:
            dict: KubeOVN VPC object
        """
        try:
            vpc = get_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=vpc_name
            )
            logging(f"Retrieved KubeOVN VPC {vpc_name}")
            return vpc
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN VPC {vpc_name} does not exist")
                return None
            raise Exception(f"Failed to get KubeOVN VPC {vpc_name}: {err}") from err

    def create_vpc(self, vpc_name, **kwargs):
        """
        Create new KubeOVN VPC

        Args:
            vpc_name: Name of new KubeOVN VPC
            **kwargs: Additional parameters as keyword arguments

        Returns:
            dict: KubeOVN VPC object
        """
        try:
            enable_external = kwargs.get("enableExternal", None)
            body = {
                "apiVersion": f"{self.group}/{self.version}",
                "kind": "Vpc",
                "metadata": {
                    "name": vpc_name,
                    "labels": {
                        "harvesterhci.io/creator": "robot-framework",
                    },
                },
                "spec": {
                    "enableExternal":
                        None if enable_external is None else enable_external == "True",
                }
            }

            vpc = create_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                body=body
            )
            logging(f"Created KubeOVN VPC {vpc_name}")
            return vpc
        except ApiException as err:
            raise Exception(f"Failed to create KubeOVN VPC {vpc_name}: {err}") from err

    def delete_vpc(self, vpc_name):
        """
        Delete KubeOVN VPC

        Args:
            vpc_name: Name of KubeOVN VPC to be deleted

        Returns
            dict: The deleted KubeOVN VPC
        """
        try:
            vpc = delete_cluster_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                name=vpc_name
            )
            logging(f"Deleted KubeOVN VPC {vpc_name}")
            return vpc
        except ApiException as err:
            if err.status == 404:
                logging(f"KubeOVN VPC {vpc_name} already deleted")
                return None
            raise Exception(f"Failed to delete KubeOVN VPC {vpc_name}: {err}") from err
