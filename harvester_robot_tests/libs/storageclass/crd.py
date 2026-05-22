"""StorageClass Component: CRD Implementation

Layer 4: Makes actual Kubernetes API calls
"""

from kubernetes import client
from kubernetes.client.rest import ApiException
from constant import LABEL_TEST, LABEL_TEST_VALUE, LVM_PROVISIONER
from utility.utility import logging
from .base import Base


class CRD(Base):
    """CRD implementation for StorageClass operations using Kubernetes API"""

    def __init__(self):
        self.storage_api = client.StorageV1Api()

    def create_lvm_sc(self, sc_name, vg_name, vg_type, node):
        """Create an LVM StorageClass"""
        logging(f"Creating LVM StorageClass: {sc_name}")

        # Map internal VG-type names to the values the CSI driver accepts
        _SC_TYPE_MAP = {
            "dm-thin": "dm-thin",
            "striped": "striped",
        }
        sc_type = _SC_TYPE_MAP.get(vg_type, vg_type)

        body = client.V1StorageClass(
            api_version="storage.k8s.io/v1",
            kind="StorageClass",
            metadata=client.V1ObjectMeta(
                name=sc_name,
                labels={LABEL_TEST: LABEL_TEST_VALUE}
            ),
            provisioner=LVM_PROVISIONER,
            parameters={
                "node": node,
                "vgName": vg_name,
                "type": sc_type
            },
            reclaim_policy="Delete",
            volume_binding_mode="WaitForFirstConsumer",
            allow_volume_expansion=True,
            allowed_topologies=[
                client.V1TopologySelectorTerm(
                    match_label_expressions=[
                        client.V1TopologySelectorLabelRequirement(
                            key="topology.lvm.csi/node",
                            values=[node]
                        )
                    ]
                )
            ]
        )

        try:
            self.storage_api.create_storage_class(body=body)
            logging(f"StorageClass {sc_name} created")
        except ApiException as e:
            if e.status == 409:
                logging(f"StorageClass {sc_name} already exists")
            else:
                raise Exception(f"Failed to create StorageClass {sc_name}: {e}")

    def delete(self, sc_name):
        """Delete a StorageClass"""
        try:
            self.storage_api.delete_storage_class(name=sc_name)
            logging(f"StorageClass {sc_name} deleted")
        except ApiException as e:
            if e.status != 404:
                logging(f"Error deleting StorageClass {sc_name}: {e}")

    def get_node(self, sc_name):
        """Get the node parameter from a StorageClass"""
        try:
            sc = self.storage_api.read_storage_class(name=sc_name)
            return sc.parameters.get("node", "")
        except ApiException:
            return ""
