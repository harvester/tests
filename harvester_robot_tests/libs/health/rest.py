"""
Health REST implementation stub.
Layer 4: ComponentHealth is only exposed as a Kubernetes CRD, so the REST
strategy is not supported.
"""
from constant import DEFAULT_TIMEOUT
from health.base import Base


class Rest(Base):
    """REST strategy stub - all methods raise NotImplementedError."""

    def component_health_exists(self, name):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def get_check(self, component_health_name, check_name):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def wait_for_check_affects_resource(self, component_health_name, check_name,
                                        resource_name, timeout=DEFAULT_TIMEOUT):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def wait_for_resource_ignored_state(self, component_health_name, check_name,
                                        resource_name, ignored, timeout=DEFAULT_TIMEOUT):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def wait_for_check_ignored_state(self, component_health_name, check_name,
                                     ignored, timeout=DEFAULT_TIMEOUT):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def create_ignore_rule(self, name, component_health_name, check_name,
                           resources=None, expires_at=None, reason=None):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def expire_ignore_rule(self, name):
        raise NotImplementedError("REST strategy not yet supported for Health")

    def delete_ignore_rule(self, name):
        raise NotImplementedError("REST strategy not yet supported for Health")
