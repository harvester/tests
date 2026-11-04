"""
SupportBundle Keywords for Robot Framework
Layer 3: Keyword wrappers - creates SupportBundle component and delegates
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa: E402

from utility.utility import logging  # noqa: E402
from support_bundle import SupportBundle  # noqa: E402


class support_bundle_keywords:
    """SupportBundle keyword wrapper - creates SupportBundle component and delegates"""

    def __init__(self):
        self.support_bundle = SupportBundle()

    def create_support_bundle(self, name, description="robot test support bundle"):
        """Create a support bundle"""
        logging(f'Creating support bundle {name}')
        self.support_bundle.create(name, description)

    def delete_support_bundle(self, name):
        """Delete a support bundle, ignoring when it is already gone"""
        logging(f'Deleting support bundle {name}')
        self.support_bundle.delete(name)
