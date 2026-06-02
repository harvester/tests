""" Blockdevice Component: CRD Implementation

Layer 4: Component and its implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cr, patch_cr
from constant import HARVESTER_API_GROUP, HARVESTER_API_VERSION
from utility.utility import logging
from .base import Base


class CRD(Base):
    """CRD implementation for Blockdevice operations using Kubernetes API"""

    def __init__(self):
        """Initialize Kubernetes client"""
        super().__init__()
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.common_parameters = {
            "group": HARVESTER_API_GROUP,
            "version": HARVESTER_API_VERSION,
            "plural": "blockdevices"
        }
        self.port_forward_process = None

    def list(self, namespace):
        try:
            return self.custom_api.list_namespaced_custom_object(
                **self.common_parameters,
                namespace=namespace
            ).get("items", [])
        except ApiException as e:
            if e.status == 404:
                logging(f"No blockdevice under {namespace}", level='WARNING')
                return []
            raise Exception(f"Failed to list blockdevices under {namespace}: {e}")

    def get(self, name, namespace):
        try:
            return get_cr(
                **self.common_parameters,
                namespace=namespace,
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Blockdevice {namespace}/{name} not found", level='ERROR')
            raise Exception(f"Failed to get blockdevice: {e}")

    def provision_longhorn_storage(self, name, engine_version, namespace):
        blockdevice = self.get(name, namespace)
        if not blockdevice:
            raise Exception(f"Blockdevice {namespace}/{name} not found")

        patch_body = {
            "spec": {
                "provision": True,
                "provisioner": {
                    "longhorn": {
                        "diskDriver": "auto",
                        "engineVersion": engine_version
                    }
                }
            }
        }
        try:
            patch_cr(
                **self.common_parameters,
                namespace=namespace,
                name=name,
                body=patch_body
            )
        except ApiException as e:
            raise Exception(f"Failed to provision blockdevice {namespace}/{name}: {e}")
