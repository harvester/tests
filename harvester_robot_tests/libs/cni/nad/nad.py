import os
from constant import HarvesterOperationStrategy
from nad.rest import Rest
from nad.crd import CRD
from nad.base import Base


class NetworkAttachmentDefinition(Base):
    def __init__(self):
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.nad = CRD()
        else:
            self.nad = Rest()

    def get(self, namespace, name):
        return self.nad.get(namespace, name)

    def create(self, namespace, name, **kwargs):
        return self.nad.create(namespace, name, **kwargs)

    def delete(self, namespace, name):
        return self.nad.delete(namespace, name)
