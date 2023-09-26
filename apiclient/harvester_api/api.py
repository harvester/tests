from urllib.parse import urljoin

import requests
from pkg_resources import parse_version
from requests.packages.urllib3.util.retry import Retry

from .managers import (
    HostManager, KeypairManager, ImageManager, SettingManager,
    NetworkManager, VolumeManager, VolumeSnapshotManager, TemplateManager, SupportBundlemanager,
    ClusterNetworkManager, VirtualMachineManager, StorageClassManager,
    BackupManager, VersionManager, UpgradeManager, LonghornReplicaManager,
    LonghornVolumeManager, VirtualMachineSnapshotManager,
    LonghornBackupVolumeManager
)

from .managers import DEFAULT_NAMESPACE


class HarvesterAPI:
    API_VERSION = "harvesterhci.io/v1beta1"

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

        self._version = None

        self.endpoint = endpoint
        self.hosts = HostManager(self)
        self.keypairs = KeypairManager(self)
        self.images = ImageManager(self)
        self.networks = NetworkManager(self)
        self.volumes = VolumeManager(self)
        self.volsnapshots = VolumeSnapshotManager(self)
        self.templates = TemplateManager(self)
        self.supportbundle = SupportBundlemanager(self)
        self.settings = SettingManager(self)
        self.clusternetworks = ClusterNetworkManager(self)
        self.vms = VirtualMachineManager(self)
        self.backups = BackupManager(self)
        self.vm_snapshots = VirtualMachineSnapshotManager(self)
        self.scs = StorageClassManager(self)
        # not available in dashboard
        self.versions = VersionManager(self)
        self.upgrades = UpgradeManager(self)
        self.lhreplicas = LonghornReplicaManager(self)
        self.lhvolumes = LonghornVolumeManager(self)
        self.lhbackupvolumes = LonghornBackupVolumeManager(self)

    @property
    def cluster_version(self):
        if not self._version:
            code, data = self.settings.get('server-version')
            ver = data['value']
            try:
                # XXX: https://github.com/harvester/harvester/issues/3137
                # Fixed as:
                # 1. va.b-xxx-head => va.b.99
                # 2. master-xxx-head => v8.8.99
                cur, _, _ = ver.split('-')
                cur = "v8.8" if "master" in cur else cur
                self._version = parse_version(f"{cur}.99")
            except ValueError:
                self._version = parse_version(ver)
            # store the raw version returns from `server-version` for reference
            self._version.raw = ver
        return self._version

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

    def _patch(self, path, **kwargs):
        url = self.get_url(path)
        headers = {"Content-type": "application/merge-patch+json"}
        headers.update(kwargs.pop('headers', {}))
        return self.session.patch(url, headers=headers, **kwargs)

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
            self._version = None
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

    def get_pods(self, name="", namespace=DEFAULT_NAMESPACE):
        path = f"v1/pods/{namespace}/{name}"
        resp = self._get(path)
        return resp.status_code, resp.json()

    def get_apps_catalog(self, name="", namespace=DEFAULT_NAMESPACE):
        path = f"v1/catalog.cattle.io.apps/{namespace}/{name}"
        resp = self._get(path)
        return resp.status_code, resp.json()

    def get_crds(self, name=""):
        path = f"v1/apiextensions.k8s.io.customresourcedefinitions/{name}"
        resp = self._get(path)
        return resp.status_code, resp.json()
