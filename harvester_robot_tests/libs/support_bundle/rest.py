"""
SupportBundle REST implementation stub.
Layer 4: REST strategy is not yet supported for SupportBundle operations.
"""
from constant import HARVESTER_NAMESPACE
from support_bundle.base import Base


class Rest(Base):
    """REST strategy stub - all methods raise NotImplementedError."""

    def create(self, name, description, namespace=HARVESTER_NAMESPACE):
        raise NotImplementedError("REST strategy not yet supported for SupportBundle")

    def delete(self, name, namespace=HARVESTER_NAMESPACE):
        raise NotImplementedError("REST strategy not yet supported for SupportBundle")
