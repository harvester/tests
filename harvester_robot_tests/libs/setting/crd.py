""" Setting Component: CRD Implementation

Layer 4: Component and its implementation
"""

import json
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cr, patch_cr
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
)
from utility.utility import logging
from .base import Base


class CRD(Base):
    """CRD implementation for Setting operations using Kubernetes API"""

    def __init__(self):
        """Initialize Kubernetes client"""
        self.core_api = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.common_parameters = {
            "group": HARVESTER_API_GROUP,
            "version": HARVESTER_API_VERSION,
            "namespace": "",
            "plural": "settings"
        }
        self.port_forward_process = None

    def get(self, setting_id):
        """Get setting details by id"""
        try:
            setting = get_cr(
                **self.common_parameters,
                name=setting_id
            )
            return setting
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"Setting {setting_id} not found", level='ERROR')
            raise Exception(f"Failed to get setting {setting_id}: {e}")

    def enable(self, setting_id):
        """Enable a setting by id"""
        try:
            patch_body = {
                "value": "true"
            }
            setting = patch_cr(
                **self.common_parameters,
                name=setting_id,
                body=patch_body
            )
            return setting
        except ApiException as e:
            raise Exception(f"Failed to enable setting {setting_id}: {e}")

    def configure_csi_driver(self, setting_id, provisioner, snapshot_class):
        """Configure csi-driver-config to add a provisioner entry.
        Preserves existing entries by reading value or default fallback.
        """
        logging(f"Configuring csi-driver-config for provisioner={provisioner}")
        try:
            setting = get_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace="",
                plural="settings",
                name=setting_id
            )
        except ApiException:
            setting = self.custom_api.get_cluster_custom_object(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                plural="settings",
                name=setting_id
            )

        current_value = setting.get("value") or setting.get("default", "{}")
        try:
            config = json.loads(current_value) if current_value else {}
        except (json.JSONDecodeError, TypeError):
            config = {}

        if provisioner not in config:
            config[provisioner] = {}
        config[provisioner]["volumeSnapshotClassName"] = snapshot_class

        patch_body = {"value": json.dumps(config)}
        try:
            self.custom_api.patch_cluster_custom_object(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                plural="settings",
                name=setting_id,
                body=patch_body
            )
            logging(f"csi-driver-config updated for {provisioner}")
        except ApiException as e:
            raise Exception(f"Failed to update csi-driver-config: {e}")

    def remove_csi_driver(self, setting_id, provisioner):
        """Remove a provisioner entry from csi-driver-config setting."""
        logging(f"Removing csi-driver-config entry for provisioner={provisioner}")
        try:
            setting = get_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace="",
                plural="settings",
                name=setting_id
            )
        except ApiException:
            setting = self.custom_api.get_cluster_custom_object(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                plural="settings",
                name=setting_id
            )

        current_value = setting.get("value") or setting.get("default", "{}")
        try:
            config = json.loads(current_value) if current_value else {}
        except (json.JSONDecodeError, TypeError):
            config = {}

        if provisioner in config:
            del config[provisioner]
            patch_body = {"value": json.dumps(config)}
            try:
                self.custom_api.patch_cluster_custom_object(
                    group=HARVESTER_API_GROUP,
                    version=HARVESTER_API_VERSION,
                    plural="settings",
                    name=setting_id,
                    body=patch_body
                )
                logging(f"csi-driver-config entry removed for {provisioner}")
            except ApiException as e:
                raise Exception(f"Failed to update csi-driver-config: {e}")
        else:
            logging(f"No csi-driver-config entry found for {provisioner}, skipping")
