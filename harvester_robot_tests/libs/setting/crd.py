""" Setting Component: CRD Implementation

Layer 4: Component and its implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cluster_cr, patch_cluster_cr
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
)
from .base import Base


class CRD(Base):
    """CRD implementation for Setting operations using Kubernetes API.

    settings.harvesterhci.io are cluster-scoped CRs (no namespace), so all
    operations use the cluster-scoped API calls.
    """

    def __init__(self):
        """Initialize Kubernetes client"""
        super().__init__()
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.common_parameters = {
            "group": HARVESTER_API_GROUP,
            "version": HARVESTER_API_VERSION,
            "plural": "settings"
        }

    def get(self, setting_id):
        """Get setting details by id"""
        try:
            setting = get_cluster_cr(
                **self.common_parameters,
                name=setting_id
            )
            return setting
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Setting {setting_id} not found")
            raise Exception(f"Failed to get setting {setting_id}: {e}")

    def enable(self, setting_id):
        """Enable a setting by id"""
        try:
            patch_body = {
                "value": "true"
            }
            setting = patch_cluster_cr(
                **self.common_parameters,
                name=setting_id,
                body=patch_body
            )
            return setting
        except ApiException as e:
            raise Exception(f"Failed to enable setting {setting_id}: {e}")

    def update(self, setting_id, value):
        """Update a setting's value by id"""
        try:
            patch_body = {
                "value": value
            }
            setting = patch_cluster_cr(
                **self.common_parameters,
                name=setting_id,
                body=patch_body
            )
            return setting
        except ApiException as e:
            raise Exception(f"Failed to update setting {setting_id}: {e}")
