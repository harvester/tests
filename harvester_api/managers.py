import json
from weakref import ref


class BaseManager:
    def __init__(self, api):
        self._api = ref(api)

    @property
    def api(self):
        if self._api() is None:
            raise ReferenceError("API object no longer exists")
        return self._api()

    def _get(self, call, *, raw=False, **kwargs):
        resp = self.api._get(call, **kwargs)
        if raw:
            return resp
        try:
            return resp.json()
        except json.decoder.JSONDecodeError as e:
            return dict(error=e)

    def _create(self, call, **kwargs):
        return self.api._post(call, **kwargs)

    def _update(self, call, **kwargs):
        return self.api._put(call, **kwargs)

    def _delete(self, call, **kwargs):
        return self.api._delete(call, **kwargs)

    def _inject_data(self, data):
        s = json.dumps(data).format(API_VERSION=self.api.API_VERSION)
        return json.loads(s)


class KubevirtAPI:
    API_VERSION = "kubevirt.io/v1"
    RESOURCE_VERSION = "subresources.kubevirt.io/v1"

    # get, create, update, delete
    vm = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachines/{uid}"
    # operators: start, restart, stop, migrate
    vm_operator = "apis/{RESOURCE_VERSION}/namespaces/{namespaces}/virtualmachines/{uid}/{operator}"
    # get
    vminstance = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachineinstances/{uid}"
    # operators: pause, unpause
    vminstance_operator = "apis/{RESOURCE_VERSION}/namespaces/{namespaces}/virtualmachineinstances/{uid}/{operator}"


class HostManager(BaseManager):
    PATH_fmt = "v1/nodes/{uid}"
    METRIC_fmt = "v1/metrics.k8s.io.nodes/{uid}"

    def get(self, name="", raw=False):
        return super()._get(self.PATH_fmt.format(uid=name))

    def create(self, *args, **kwargs):
        raise NotImplementedError("Create is not allowed.")

    def update(self, name, data):
        raise NotImplementedError()

    def delete(self, name):
        return super()._delete(self.PATH_fmt.format(uid=name))

    def get_metrics(self, name=""):
        return super()._get(self.METRIC_fmt.format(uid=name))


class ImageManager(BaseManager):
    # get, create, update, delete
    PATH_fmt = "apis/{{API_VERSION}}/namespaces/{ns}/virtualmachineimages/{uid}"
    _KIND = "VirtualMachineImage"

    def create_data(name, url, desc, stype, namespace, display_name=None):
        data = {
            "apiVersion": "{API_VERSION}",
            "kind": self._KIND,
            "metadata": {
                "annotations": {
                    "field.cattle.io/description": desc
                },
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "displayName": display_name or name,
                "sourceType": stype,
                "url": url
            }
        }
        return super()._inject_data(data)

    def get(self, name="", namespace="default"):
        return super()._get(self.PATH_fmt.format(uid=name, ns=namespace))

    def create(self, name, url, description="", source_type="download", namespace="default"):
        data = self.create_data(name, url, description, source_type, namespace)
        return self._create(PATH_fmt.format(uid="", ns=namespace), json=data)


class VolumeManager:
    # get, create, update, delete
    volume = "api/v1/namespaces/{ns}/persistentvolumeclaims/{uid}"


class VirtualMachineManager:
    pass


class TemplateManager:
    # get, create, delete
    vm_template = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachinetemplates/{uid}"
    vm_template_version = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachinetemplateversions/{uid}"


class backupManager:
    # get, create, update, delete
    backup = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachinebackups/{uid}"


class KeypairManager:
    # get, create, delete
    keypair = "apis/{API_VERSION}/namespaces/{namespaces}/keypairs/{uid}"


class NetworkManager:
    # get, create, update, delete
    network = "v1/k8s.cni.cncf.io.network-attachment-definitions/{uid}"


class SettingManager:
    # get, update
    vlan = "apis/network.{API_VERSION}/clusternetworks/vlan"
    # api-ui-version, backup-target, cluster-registration-url
    settings = "v1/harvesterhci.io.settings/{option}"

