"""
Template CRD Implementation
Uses Kubernetes Custom Resources for VirtualMachineTemplate operations
"""
from kubernetes.client.rest import ApiException
from crd import get_cr, list_cr
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    VIRTUALMACHINETEMPLATE_PLURAL, VIRTUALMACHINETEMPLATEVERSION_PLURAL,
    HARVESTER_PUBLIC_NAMESPACE,
)
from vm_template.base import Base


class CRD(Base):
    """
    Template CRD implementation
    Uses harvesterhci.io/v1beta1 VirtualMachineTemplate(Version) CRDs
    """

    def list_templates(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List VirtualMachineTemplates in a namespace"""
        data = list_cr(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINETEMPLATE_PLURAL,
        )
        return data.get('items', [])

    def list_template_versions(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List VirtualMachineTemplateVersions in a namespace"""
        data = list_cr(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINETEMPLATEVERSION_PLURAL,
        )
        return data.get('items', [])

    def try_get_template(self, template_name, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """Attempt to get a template; returns {success, code, message}."""
        try:
            get_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINETEMPLATE_PLURAL,
                name=template_name,
            )
            return {"success": True, "code": 200, "message": ""}
        except ApiException as e:
            return {"success": False, "code": e.status,
                    "message": e.body or e.reason or ""}
