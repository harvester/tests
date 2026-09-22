"""
KubeOVN Subnet Keywords
"""

import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../kubeovn'))) # noqa E402
from utility.utility import logging  # noqa E402
from kubeovn import Subnet # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402


class kubeovn_subnet_keywords:
    """
    KubeOVN Subnet keyword wrapper
    """

    def __init__(self):
        self._subnet = None

    @property
    def subnet(self):
        if self._subnet is None:
            self._subnet = Subnet()
        return self._subnet

    def create_subnet(self, name, **kwargs):
        """
        Create KubeOVN Subnet
        """
        return self.subnet.create_subnet(name, **kwargs)

    def get_subnet(self, name):
        """
        Get KubeOVN Subnet details

        Args:
            name: Name of the KubeOVN subnet

        Returns:
            dict: KubeOVN Subnet Object
        """
        return self.subnet.get(name)

    def delete_subnet(self, name):
        return self.subnet.delete(name)
