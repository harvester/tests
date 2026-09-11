"""
KubeOVN VPC Keywords
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../kubeovn'))) # noqa E402
from utility.utility import logging  # noqa E402
from kubeovn import VPC # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402

class kubeovn_vpc_keywords:
    """
    KubeOVN VPC keyword wrapper
    """
    def __init__(self):
        self._vpc = None

    @property
    def vpc(self):
        if self._vpc is None:
            self._vpc = VPC()
        return self._vpc

    def get_vpc(self, vpc_name):
        """
        Get VPC details

        Args:
            vpc_name: Name of the KubeOVN VPC

        Returns:
            dict: KubeOVN VPC Object
        """
        return self.vpc.get_vpc(vpc_name)
