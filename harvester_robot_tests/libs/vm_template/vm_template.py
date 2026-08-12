"""
VMTemplate Component - delegates to CRD or REST implementation
Layer 4: Selects implementation based on strategy

The implementation is selected based on the HARVESTER_OPERATION_STRATEGY
environment variable. Valid values are 'crd' or 'rest'. Defaults to 'crd' if not set.
"""

import os
from constant import HarvesterOperationStrategy, HARVESTER_PUBLIC_NAMESPACE
from vm_template.rest import Rest
from vm_template.crd import CRD
from vm_template.base import Base


class VMTemplate(Base):
    """
        VMTemplate component that delegates to CRD or REST implementation

        The implementation is selected based on:
        - HARVESTER_OPERATION_STRATEGY environment variable ('crd' or 'rest')
        - Defaults to 'crd' if not set
    """

    def __init__(self):
        """Initialize VMTemplate component"""
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.vm_template = CRD()
        else:
            self.vm_template = Rest()

    def list_templates(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List templates - delegates to implementation"""
        return self.vm_template.list_templates(namespace)

    def list_template_versions(self, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """List template versions - delegates to implementation"""
        return self.vm_template.list_template_versions(namespace)

    def try_get_template(self, template_name, namespace=HARVESTER_PUBLIC_NAMESPACE):
        """Attempt to get a template - delegates to implementation"""
        return self.vm_template.try_get_template(template_name, namespace)
