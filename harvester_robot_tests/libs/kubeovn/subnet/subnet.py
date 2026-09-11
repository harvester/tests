import os
from constant import HarvesterOperationStrategy
from subnet.rest import Rest
from subnet.crd import CRD
from subnet.base import Base


class Subnet(Base):
    def __init__(self):
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.subnet = CRD()
        else:
            self.subnet = Rest()

    def create_subnet(self, name):
        return self.subnet.create_subnet(name)

    def get_subnet(self, name):
        return self.subnet.get_subnet(name)

    def delete_subnet(self, name):
        return self.subnet.delete_subnet(name)
