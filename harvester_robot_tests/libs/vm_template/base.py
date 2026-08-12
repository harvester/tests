"""
Base class for VM template operations
"""
from abc import ABC, abstractmethod


class Base(ABC):
    """Base class for VM template implementations"""

    @abstractmethod
    def list_templates(self, namespace):
        """List VirtualMachineTemplates in a namespace, returns list of dicts"""
        pass

    @abstractmethod
    def list_template_versions(self, namespace):
        """List VirtualMachineTemplateVersions in a namespace, returns list of dicts"""
        pass

    @abstractmethod
    def try_get_template(self, template_name, namespace):
        """Attempt to get a template; returns {success, code, message}"""
        pass
