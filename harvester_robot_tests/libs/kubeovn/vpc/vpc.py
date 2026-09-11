import os
from constant import HarvesterOperationStrategy
from vpc.rest import Rest
from vpc.crd import CRD
from vpc.base import Base


class VPC(Base):
    def __init__(self):
        # Get strategy from environment variable, default to CRD
        strategy_str = os.getenv("HARVESTER_OPERATION_STRATEGY", "crd").lower()
        try:
            self._strategy = HarvesterOperationStrategy(strategy_str)
        except ValueError:
            # If invalid value, default to CRD
            self._strategy = HarvesterOperationStrategy.CRD

        if self._strategy == HarvesterOperationStrategy.CRD:
            self.vpc = CRD()
        else:
            self.vpc = Rest()

    def get_vpc(self, vpc_name):
        """
        Get KubeOVN VPC details
        """
        return self.vpc.get_vpc(vpc_name)
