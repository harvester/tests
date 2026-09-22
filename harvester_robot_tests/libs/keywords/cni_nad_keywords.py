"""
CNI NetworkAttachmentDefinition Keywords
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../cni'))) # noqa E402
from utility.utility import logging  # noqa E402
from cni import NetworkAttachmentDefinition # noqa E402
from constant import DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_LONG  # noqa E402


class cni_nad_keywords:
    def __init__(self):
        self._nad = None

    @property
    def nad(self):
        if self._nad is None:
            self._nad = NetworkAttachmentDefinition()
        return self._nad

    def get_nad(self, namespace, name):
        return self.nad.get(namespace, name)

    def create_nad(self, namespace, name, **kwargs):
        return self.nad.create(namespace, name, **kwargs)

    def delete_nad(self, namespace, name):
        return self.nad.delete(namespace, name)
