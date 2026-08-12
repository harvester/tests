"""
Template Rest Implementation - makes actual API calls using get_harvester_api_client()
"""
from utility.utility import get_harvester_api_client
from constant import HARVESTER_PUBLIC_NAMESPACE
from vm_template.base import Base


class Rest(Base):
    """Template Rest implementation - makes actual API calls"""

    def list_templates(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List VirtualMachineTemplates in a namespace"""
        api = get_harvester_api_client()
        code, data = api.templates.get(namespace=namespace)
        assert code == 200, f"Failed to list templates: {code}, {data}"
        return data.get('items', [])

    def list_template_versions(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List VirtualMachineTemplateVersions in a namespace"""
        api = get_harvester_api_client()
        code, data = api.templates.get_version(namespace=namespace)
        assert code == 200, f"Failed to list template versions: {code}, {data}"
        return data.get('items', [])

    def try_get_template(self, template_name, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """Attempt to get a template; returns {success, code, message}."""
        api = get_harvester_api_client()
        code, data = api.templates.get(template_name, namespace=namespace)
        if code == 200:
            return {"success": True, "code": code, "message": ""}
        if isinstance(data, dict):
            # keep the reason (e.g. NotFound) - the k8s message alone spells
            # it "not found", which assertions on the reason would miss
            message = " ".join(
                str(part) for part in (data.get('reason'), data.get('message')) if part
            )
        else:
            message = str(data)
        return {"success": False, "code": code, "message": message}
