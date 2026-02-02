# Copyright (c) 2024 SUSE LLC
#
# pylint: disable=missing-function-docstring

from urllib.parse import urljoin

import kubernetes
import requests
import yaml


class KubeAPI:
    """
    An abstraction of the Kubernetes API.

    Example usage:

    ```
    with KubeAPI(endpoint, tls_verify=false) as api:
      api.authenticate(username, password, verify=false)
      kube_client = api.get_client()

      corev1 = kubernetes.client.CoreV1Api(kube_client)

      namespaces = corev1.list_namespace()
    ```
    """

    HARVESTER_API_VERSION = "harvesterhci.io/v1beta1"

    def __init__(self, endpoint, tls_verify, token=None, session=None):
        self.session = session or requests.Session()
        self.session.verify = tls_verify
        self.session.headers.update(Authorization=token or "")

        self.endpoint = endpoint

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, taceback):
        pass

    def _post(self, path, **kwargs):
        url = self._get_url(path)
        return self.session.post(url, **kwargs)

    def _get_url(self, path):
        return urljoin(self.endpoint, path).format(API_VERSION=self.HARVESTER_API_VERSION)

    def get_client(self):
        path = "/v1/management.cattle.io.clusters/local"
        params = {"action": "generateKubeconfig"}

        resp = self._post(path, params=params)
        assert resp.status_code == 200, "Failed to generate kubeconfig"

        kubeconfig = yaml.safe_load(resp.json()['config'])
        return kubernetes.config.new_client_from_config_dict(kubeconfig)

    def authenticate(self, user, passwd, **kwargs):
        path = "v3-public/localProviders/local?action=login"
        resp = self._post(path, json=dict(username=user, password=passwd), **kwargs)

        assert resp.status_code == 201, "Failed to authenticate"

        token = f"Bearer {resp.json()['token']}"
        self.session.headers.update(Authorization=token)

        return resp.json()
