"""
KubeOVN VPC CRD implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cluster_cr, patch_cr
from constant import (
    DEFAULT_TIMEOUT,
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
        self.vpc_group = KUBEOVN_API_GROUP
        self.vpc_version = KUBEOVN_API_VERSION
        self.vpc_plural = KUBEOVN_VPC_PLURAL

    def get_vpc(self, vpc_name):
        """
        Get KubeOVN VPC details

        Args:
            vpc_name: Name of the vpc

        Returns:
            dict: KubeOVN VPC object
        """
        try:
            vpc = get_cluster_cr(
                group=self.vpc_group,
                version=self.vpc_version,
                plural=self.vpc_plural,
                name=vpc_name
            )
            logging(f"Retrieved KubeOVN VPC {vpc_name}")
            return vpc
        except ApiException as err:
            raise Exception(f"Failed to get KubeOVN VPC {vpc_name}: {err}") from err
