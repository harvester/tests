""" ConfigMap Component: CRD Implementation

Layer 4: Component and its implementation
"""

from kubernetes import client
from kubernetes.client.rest import ApiException

from constant import LABEL_TEST, LABEL_TEST_VALUE
from utility.utility import logging
from configmap.base import Base


class CRD(Base):
    """CRD implementation for ConfigMap operations using the Kubernetes API"""

    def create(self, name, namespace, labels=None, data=None):
        body = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=name, namespace=namespace,
                labels={LABEL_TEST: LABEL_TEST_VALUE, **(labels or {})}),
            data=data)
        client.CoreV1Api().create_namespaced_config_map(namespace=namespace, body=body)
        logging(f"Created config map {namespace}/{name}")

    def delete(self, name, namespace):
        try:
            client.CoreV1Api().delete_namespaced_config_map(name=name, namespace=namespace)
            logging(f"Deleted config map {namespace}/{name}")
        except ApiException as e:
            if e.status != 404:
                raise
