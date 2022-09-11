from urllib.parse import urljoin

import requests
from requests.packages.urllib3.util.retry import Retry

from .managers import HostManager, KeypairManager, ImageManager


class HarvesterAPI:
    API_VERSION = "harvesterhci.io/v1beta1"

    _supportbundle = ("apis/{{API_VERSION}}/namespaces/harvester-system"
                      "/supportbundles/{uid}{download}")

    # not used
    first_login = "v1/management.cattle.io.setting/first-login"
    reset_password = "v3/users"
    upload_image = "v1/harvester/harvesterhci.io.virtualmachineimages/{namespaces}/{uid}"
    user = "v1/harvesterhci.io.users"

    @classmethod
    def login(cls, endpoint, user, passwd, session=None, ssl_verify=True):
        api = cls(endpoint, session=session)
        api.authenticate(user, passwd, verify=ssl_verify)

        return api

    def __init__(self, endpoint, token=None, session=None):
        self.session = session or requests.Session()
        self.session.headers.update(Authorization=token or "")

        if session is None:
            self.set_retries()

        self.endpoint = endpoint
        self.hosts = HostManager(self)
        self.keypairs = KeypairManager(self)
        self.images = ImageManager(self)

    def __repr__(self):
        return f"HarvesterAPI({self.endpoint!r}, {self.session.headers['Authorization']!r})"

    def _get(self, path, **kwargs):
        url = self.get_url(path)
        return self.session.get(url, **kwargs)

    def _post(self, path, **kwargs):
        url = self.get_url(path)
        return self.session.post(url, **kwargs)

    def _put(self, path, **kwargs):
        url = self.get_url(path)
        return self.session.put(url, **kwargs)

    def _delete(self, path, **kwargs):
        url = self.get_url(path)
        return self.session.delete(url, **kwargs)

    def get_url(self, path):
        return urljoin(self.endpoint, path).format(API_VERSION=self.API_VERSION)

    def authenticate(self, user, passwd, **kwargs):
        path = "v3-public/localProviders/local?action=login"
        r = self._post(path, json=dict(username=user, password=passwd), **kwargs)
        try:
            assert r.status_code == 201, "Failed to authenticate"
        except AssertionError:
            pass  # TODO: Log authenticate error
        else:
            token = "Bearer %s" % r.json()['token']
            self.session.headers.update(Authorization=token)
        return r.json()

    def set_retries(self, times=5, status_forcelist=(500, 502, 504), **kwargs):
        kwargs.update(backoff_factor=kwargs.get('backoff_factor', 10.0),
                      total=kwargs.get('total', times),
                      status_forcelist=status_forcelist)
        retry_strategy = Retry(**kwargs)
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def generate_kubeconfig(self):
        path = "v1/management.cattle.io.clusters/local?action=generateKubeconfig"
        r = self._post(path)
        return r.json()['config']

    def get_support_bundle(self, uid="", download=False):
        pass

    def create_support_bundle(self):
        pass

    def delete_support_bundle(self, uid):
        pass
