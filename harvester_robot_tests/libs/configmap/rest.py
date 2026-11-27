""" ConfigMap Component: REST Implementation

Layer 4: Component and its implementation
"""

from constant import LABEL_TEST, LABEL_TEST_VALUE
from utility.utility import get_harvester_api_client, logging
from configmap.base import Base

PATH = "v1/harvester/configmaps"


class Rest(Base):
    """REST implementation for ConfigMap operations using the Harvester API"""

    @property
    def api(self):
        return get_harvester_api_client()

    def create(self, name, namespace, labels=None, data=None):
        body = {
            "type": "configmap",
            "metadata": {
                "name": name, "namespace": namespace,
                "labels": {LABEL_TEST: LABEL_TEST_VALUE, **(labels or {})}},
        }
        if data:
            body["data"] = data
        code, resp = self.api.post(PATH, body)
        assert code == 201, f"Failed to create config map {namespace}/{name}: {code}, {resp}"
        logging(f"Created config map {namespace}/{name}")

    def delete(self, name, namespace):
        code, resp = self.api.delete(f"{PATH}/{namespace}/{name}")
        assert code in (200, 204, 404), \
            f"Failed to delete config map {namespace}/{name}: {code}, {resp}"
