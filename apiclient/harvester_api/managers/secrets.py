import base64
from .base import BaseManager, DEFAULT_NAMESPACE


class SecretManager(BaseManager):
    PATH_fmt = "v1/secrets"

    def create_data(self, name, namespace, data, annotations=None):
        annotations = annotations or {}
        encoded_data = {
            k: base64.b64encode(v.encode('utf-8')).decode('utf-8')
            for k, v in data.items()
        }

        return {
            "type": "secret",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations
            },
            "data": encoded_data
        }

    def create(self, name, data, namespace=DEFAULT_NAMESPACE, annotations=None, *, raw=False):
        secret_data = self.create_data(name, namespace, data, annotations=annotations)
        return self._create(self.PATH_fmt, json=secret_data, raw=raw)

    def get(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = f"{self.PATH_fmt}/{namespace}/{name}"
        return self._get(path, raw=raw)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = f"{self.PATH_fmt}/{namespace}/{name}"
        return self._delete(path, raw=raw)
