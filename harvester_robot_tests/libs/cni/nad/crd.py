"""
CNI NetworkAttachmentDefinition CRD implementation
"""

import json
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import create_cr, delete_cr, get_cr
from constant import (
    CNI_GROUP,
    CNI_VERSION,
    CNI_NAD_PLURAL,
)
from utility.utility import logging
from nad.base import Base


class CRD(Base):
    def __init__(self):
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.group = CNI_GROUP
        self.version = CNI_VERSION
        self.plural = CNI_NAD_PLURAL

    def get(self, namespace, name):
        try:
            nad = get_cr(
                group=self.group,
                version=self.version,
                plural=self.plural,
                namespace=namespace,
                name=name
            )
            logging(f"Retrieved CNI NetworkAttachmentDefinition {namespace}/{name}")
            return nad
        except ApiException as err:
            if err.status == 404:
                logging(f"CNI NetworkAttachmentDefinition {namespace}/{name} not found")
                return None
            raise Exception(f"Failed to get CNI NetworkAttachmentDefinition {namespace}/{name}:"
                            f"{err}") from err

    def create(self, namespace, name, **kwargs):
        try:
            nad_type = kwargs.get("nad_type", "UntaggedNetwork")
            if nad_type == "OverlayNetwork":
                provider = kwargs.get("provider", "")
                master = kwargs.get("master", None)

                cni_config = {
                    "cniVersion": "0.3.1",
                    "name": name,
                    "type": "kube-ovn",
                    "server_socket": "/run/openvswitch/kube-ovn-daemon.sock",
                    "provider": provider,
                }

                if master is not None:
                    cni_config["master"] = master

                body = {
                    "apiVersion": f"{self.group}/{self.version}",
                    "kind": "NetworkAttachmentDefinition",
                    "metadata": {
                        "name": name,
                        "namespace": namespace,
                        "labels": {
                            "harvesterhci.io/creator": "robot-framework",
                            "network.harvesterhci.io/type": "OverlayNetwork",
                        },
                    },
                    "spec": {
                        "config": json.dumps(cni_config),
                    },
                }
            elif nad_type == "L2VlanNetwork":
                pass
            elif nad_type == "UntaggedNetwork":
                pass
            else:
                raise Exception(f"Unknown NetworkAttachmentDefinition type {type}")

            nad = create_cr(
                group=self.group,
                version=self.version,
                namespace=namespace,
                plural=self.plural,
                body=body
            )
            logging(f"Created CNI NetworkAttachmentDefinition {namespace}/{name}")
            return nad
        except ApiException as err:
            raise Exception(f"{err}") from err

    def delete(self, namespace, name):
        try:
            nad = delete_cr(
                group=self.group,
                version=self.version,
                namespace=namespace,
                plural=self.plural,
                name=name
            )
            logging(f"Deleted CNI NetworkAttachmentDefinition {namespace}/{name}")
            return nad
        except ApiException as err:
            raise Exception(f"{err}") from err
