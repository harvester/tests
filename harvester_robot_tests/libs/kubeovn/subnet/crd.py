"""
KubeOVN Subnet CRD implementation
"""


from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cluster_cr, patch_cr
from constant import (
    DEFAULT_TIMEOUT,
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

    def create_subnet(self, name):
        pass

    def get_subnet(self, name):
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
            raise Exception(f"Failed to get KubeOVN Subnet {name}: {err}") from err

    def delete_subnet(self, name):
        pass
