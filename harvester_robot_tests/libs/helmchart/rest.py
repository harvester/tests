"""
HelmChart REST implementation stub.
Layer 4: REST strategy is not yet supported for HelmChart operations.
"""
from constant import DEFAULT_TIMEOUT_LONG
from helmchart.base import Base


class Rest(Base):
    """REST strategy stub — all methods raise NotImplementedError."""

    def create(self, name, namespace, spec):
        raise NotImplementedError("REST strategy not yet supported for HelmChart")

    def wait_for_deployed(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        raise NotImplementedError("REST strategy not yet supported for HelmChart")

    def delete(self, name, namespace, timeout=DEFAULT_TIMEOUT_LONG):
        raise NotImplementedError("REST strategy not yet supported for HelmChart")
