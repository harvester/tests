"""
SupportBundle CRD Implementation - Kubernetes API operations
Layer 4: SupportBundle lives in harvester-system (harvesterhci.io/v1beta1).
"""
from kubernetes.client.rest import ApiException

from constant import (
    HARVESTER_API_GROUP,
    HARVESTER_API_VERSION,
    HARVESTER_NAMESPACE,
    SUPPORTBUNDLE_PLURAL,
)
from crd import create_cr, delete_cr
from support_bundle.base import Base
from utility.utility import logging


class CRD(Base):
    """CRD implementation for SupportBundle operations using Kubernetes API"""

    def create(self, name, description, namespace=HARVESTER_NAMESPACE):
        logging(f"Creating SupportBundle {namespace}/{name}")
        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "SupportBundle",
            "metadata": {"name": name, "namespace": namespace},
            "spec": {"description": description},
        }
        return create_cr(
            HARVESTER_API_GROUP, HARVESTER_API_VERSION,
            namespace, SUPPORTBUNDLE_PLURAL, body)

    def delete(self, name, namespace=HARVESTER_NAMESPACE):
        logging(f"Deleting SupportBundle {namespace}/{name}")
        try:
            delete_cr(
                HARVESTER_API_GROUP, HARVESTER_API_VERSION,
                namespace, SUPPORTBUNDLE_PLURAL, name)
        except ApiException as e:
            if e.status != 404:
                raise
