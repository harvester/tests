import json
from weakref import ref
from pathlib import Path
from collections.abc import Mapping

from pkg_resources import parse_version

DEFAULT_NAMESPACE = "default"


def merge_dict(src, dest):
    for k, v in src.items():
        if isinstance(dest.get(k), dict) and isinstance(v, dict):
            merge_dict(v, dest[k])
        else:
            dest[k] = v
    return dest


class BaseManager:
    def __init__(self, api):
        self._api = ref(api)

    @property
    def api(self):
        if self._api() is None:
            raise ReferenceError("API object no longer exists")
        return self._api()

    def _delegate(self, meth, path, *, raw=False, **kwargs):
        func = getattr(self.api, meth)
        resp = func(path, **kwargs)

        if raw:
            return resp
        try:
            return resp.status_code, resp.json()
        except json.decoder.JSONDecodeError as e:
            return resp.status_code, dict(error=e, response=resp)

    def _get(self, path, *, raw=False, **kwargs):
        return self._delegate("_get", path, raw=raw, **kwargs)

    def _create(self, path, *, raw=False, **kwargs):
        return self._delegate("_post", path, raw=raw, **kwargs)

    def _update(self, path, data, *, raw=False, as_json=True, **kwargs):
        if as_json:
            kwargs.update(json=data)
        else:
            kwargs.update(data=data)

        return self._delegate("_put", path, raw=raw, **kwargs)

    def _delete(self, path, *, raw=False, **kwargs):
        return self._delegate("_delete", path, raw=raw, **kwargs)

    def _inject_data(self, data):
        s = json.dumps(data).replace("{API_VERSION}", self.api.API_VERSION)
        return json.loads(s)


class KubevirtAPI:
    API_VERSION = "kubevirt.io/v1"
    RESOURCE_VERSION = "subresources.kubevirt.io/v1"

    # get, create, update, delete
    vm = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachines/{uid}"
    # operators: start, restart, stop, migrate
    vm_operator = ("apis/{RESOURCE_VERSION}/namespaces/{namespaces}/"
                   "virtualmachines/{uid}/{operator}")
    # get
    vminstance = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachineinstances/{uid}"
    # operators: pause, unpause
    vminstance_operator = ("apis/{RESOURCE_VERSION}/namespaces/{namespaces}/"
                           "virtualmachineinstances/{uid}/{operator}")


class HostManager(BaseManager):
    PATH_fmt = "v1/harvester/nodes/{uid}"
    METRIC_fmt = "v1/metrics.k8s.io.nodes/{uid}"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)

    def create(self, *args, **kwargs):
        raise NotImplementedError("Create new host is not allowed.")

    def update(self, name, data, *, raw=False, as_json=True, **kwargs):
        path = self.PATH_fmt.format(uid=name)
        if isinstance(data, Mapping) and as_json:
            _, node = self.get(name)
            data = merge_dict(data, node)
        return self._update(path, data, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name), raw=raw)

    def get_metrics(self, name="", *, raw=False):
        return self._get(self.METRIC_fmt.format(uid=name), raw=raw)

    def maintenance_mode(self, name, enable=True):
        action = "enable" if enable else "disable"
        params = dict(action=f"{action}MaintenanceMode")
        self._create(self.PATH_fmt.format(uid=name), params=params)
        return self.get(name)


class ImageManager(BaseManager):
    # get, create, update, delete
    PATH_fmt = "apis/{{API_VERSION}}/namespaces/{ns}/virtualmachineimages/{uid}"
    UPLOAD_fmt = "v1/harvester/harvesterhci.io.virtualmachineimages/{ns}/{uid}"
    _KIND = "VirtualMachineImage"

    def create_data(self, name, url, desc, stype, namespace, display_name=None):
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
        return self._inject_data(data)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name, ns=namespace), raw=raw)

    def create(self, name, namespace=DEFAULT_NAMESPACE, **kwargs):
        return self._create(self.PATH_fmt.format(uid=name, ns=namespace), **kwargs)

    def create_by_url(self, name, url, namespace=DEFAULT_NAMESPACE,
                      description="", display_name=None):
        data = self.create_data(name, url, description, "download", namespace, display_name)
        return self.create("", namespace, json=data)

    def create_by_file(self, name, filepath, namespace=DEFAULT_NAMESPACE,
                       description="", display_name=None):
        file = Path(filepath)

        data = self.create_data(name, "", description, "upload", namespace, display_name)
        self.create("", namespace, json=data)

        kwargs = {
            "params": dict(action="upload", size=file.stat().st_size),
            "files": dict(chunk=file.open('rb')),
        }
        return self._create(self.UPLOAD_fmt.format(uid=name, ns=namespace), raw=True, **kwargs)

    def update(self, name, data, *, raw=False, as_json=True, **kwargs):
        if isinstance(data, Mapping) and as_json:
            _, curr = self.get(name)
            data = merge_dict(data, curr)

        ns = data.get("metadata", {}).get("namespace", DEFAULT_NAMESPACE)
        path = self.PATH_fmt.format(uid=name, ns=ns)
        return self._update(path, data, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name, ns=namespace))


class VolumeManager(BaseManager):
    API_VERSION = "v1"
    # get, create, update, delete
    PATH_fmt = "api/{VOLUME_API}/namespaces/{ns}/persistentvolumeclaims/{uid}"
    _KIND = "PersistentVolumeClaim"

    def create_data(self, name, size, namespace=DEFAULT_NAMESPACE,
                    storage_cls=None, annotations=None):
        data = {
            "apiVersion": self.API_VERSION,
            "kind": self._KIND,
            "metadata": {
                "name": name,
                "namespace": namespace,
                "annotations": annotations or {}
            },
            "spec": {
                "resources": {
                    "requests": {
                        "storage": f"{size}Gi"
                    }
                },
                "volumeMode": "Block",
                "accessModes": [
                    "ReadWriteMany"
                ],
                "storageClassName": storage_cls or "longhorn"
            }
        }
        return self._inject_data(data)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace, VOLUME_API=self.API_VERSION)
        return self._get(path, raw=raw)

    def create(self, name, size, namespace=DEFAULT_NAMESPACE,
               storage_cls=None, annotations=None, raw=False):
        data = self.create_data(name, size, namespace, storage_cls, annotations)
        path = self.PATH_fmt.format(uid="", ns=namespace, VOLUME_API=self.API_VERSION)
        return self._create(path, json=data, raw=raw)

    def update(self, name, data, namespace=DEFAULT_NAMESPACE, *,
               raw=False, as_json=True, **kwargs):
        path = self.PATH_fmt.format(uid=name, ns=namespace, VOLUME_API=self.API_VERSION)
        if isinstance(data, Mapping) and as_json:
            _, node = self.get(name)
            data = merge_dict(data, node)
        return self._update(path, data, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace, VOLUME_API=self.API_VERSION)
        return self._delete(path, raw=raw)


class VirtualMachineManager(BaseManager):
    pass


class TemplateManager(BaseManager):
    # get, create, delete
    PATH_fmt = "apis/{{API_VERSION}}/namespaces/{ns}/virtualmachinetemplates/{uid}"
    VER_PATH_fmt = "apis/{{API_VERSION}}/namespaces/{ns}/virtualmachinetemplateversions/{uid}"
    _KIND = "VirtualMachineTemplate"
    _VER_KIND = "VirtualMachineTemplateVersion"

    def create_data(self, name, namespace, description):
        data = {
            "apiVersion": "{API_VERSION}",
            "kind": self._KIND,
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "description": description
            }
        }
        return self._inject_data(data)

    def create_version_data(self, name, namespace, cpu, mem, disk_name):
        data = {
            "apiVersion": "{API_VERSION}",
            "kind": self._VER_KIND,
            "metadata": {
                "generateName": f"{name}-",
                "labels": {
                    "template.harvesterhci.io/templateID": name
                },
                "namespace": namespace
            },
            "spec": {
                "templateId": f"{namespace}/{name}",
                "vm": {
                    "metadata": {
                        "annotations": {
                            "harvesterhci.io/volumeClaimTemplates": json.dumps([{
                                "metadata": {
                                    "annotations": {"harvesterhci.io/imageId": ""},
                                    "name": f"-{disk_name}"
                                },
                                "spec": {
                                    "accessModes": ["ReadWriteMany"],
                                    "resources": {"requests": {"storage": "10Gi"}},
                                    "volumeMode": "Block"
                                }
                            }])
                        }
                    },
                    "spec": {
                        "runStrategy": "RerunOnFailure",
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "harvesterhci.io/sshNames": "[]"
                                }
                            },
                            "spec": {
                                "domain": {
                                    "cpu": {
                                        "cores": cpu,
                                        "sockets": 1,
                                        "threads": 1
                                    },
                                    "devices": {
                                        "disks": [
                                            {
                                                "disk": {"bus": "virtio"},
                                                "name": "disk-0"
                                            }
                                        ],
                                        "inputs": [
                                            {
                                                "bus": "usb",
                                                "name": "tablet",
                                                "type": "tablet"
                                            }
                                        ],
                                        "interfaces": [
                                            {
                                                "masquerade": {},
                                                "model": "virtio",
                                                "name": "default"
                                            }
                                        ]
                                    },
                                    "features": {"acpi": {"enabled": True}},
                                    "machine": {
                                        "type": ""
                                    },
                                    "resources": {
                                        "requests": {
                                            "memory": mem
                                        }
                                    }
                                },
                                "evictionStrategy": "LiveMigrate",
                                "networks": [
                                    {
                                        "name": "default",
                                        "pod": {}
                                    }
                                ],
                                "volumes": [
                                    {
                                        "dataVolume": {"name": f"-{disk_name}"},
                                        "name": "disk-0"
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        return self._inject_data(data)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name, ns=namespace), raw=raw)

    def get_version(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.VER_PATH_fmt.format(uid=name, ns=namespace), raw=raw)

    def create(self, name, namespace=DEFAULT_NAMESPACE, description="", *, raw=False):
        data = self.create_data(name, namespace, description)
        path = self.PATH_fmt.format(ns=namespace, uid="")
        return self._create(path, json=data, raw=raw)

    def update(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False, **options):
        cpu, memory = options.get('cpu', 1), options.get('memory', "1Gi")
        disk_name = options.get("disk_name", "default")
        data = self.create_version_data(name, namespace, cpu, memory, disk_name)
        path = self.VER_PATH_fmt.format(uid="", ns=namespace)
        return self._create(path, json=data, raw=raw)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name, ns=namespace), raw=raw)


class BackupManager(BaseManager):
    # get, create, update, delete
    backup = "apis/{API_VERSION}/namespaces/{namespaces}/virtualmachinebackups/{uid}"


class KeypairManager(BaseManager):
    PATH_fmt = "apis/{{API_VERSION}}/namespaces/{ns}/keypairs/{uid}"
    _KIND = "KeyPair"

    def create_data(self, name, namespace, public_key):
        data = {
            "apiVersion": "{API_VERSION}",
            "kind": self._KIND,
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "publicKey": public_key
            }
        }

        return self._inject_data(data)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name, ns=namespace), raw=raw)

    def create(self, name, public_key, namespace=DEFAULT_NAMESPACE, *, raw=False):
        data = self.create_data(name, namespace, public_key)
        return self._create(self.PATH_fmt.format(uid="", ns=namespace), json=data, raw=raw)

    def update(self, *args, **kwargs):
        raise NotImplementedError("Update Keypairs is not allowed")

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace)
        return self._delete(path, raw=raw)


class NetworkManager(BaseManager):
    # get, create, update, delete
    PATH_fmt = "apis/{NETWORK_API}/namespaces/{ns}/network-attachment-definitions/{uid}"
    API_VERSION = "k8s.cni.cncf.io/v1"
    _KIND = "NetworkAttachmentDefinition"

    def _default_cluster_network(self):
        if self.api.cluster_version >= parse_version("v1.1.0"):
            return "mgmt-br"
        else:
            return "harvester-br0"

    def create_data(self, name, namespace, vlan_id, bridge_name):
        data = {
            "apiVersion": self.API_VERSION,
            "kind": self._KIND,
            "metadata": {
                "labels": {
                    "network.harvesterhci.io/type": "L2VlanNetwork"
                },
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "config": json.dumps({
                    "cniVersion": "0.3.1",
                    "name": name,
                    "type": "bridge",
                    "bridge": bridge_name,
                    "promiscMode": True,
                    "vlan": vlan_id,
                    "ipam": {}
                })
            }
        }
        return self._inject_data(data)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace, NETWORK_API=self.API_VERSION)
        return self._get(path, raw=raw)

    def create(self, name, vlan_id, namespace=DEFAULT_NAMESPACE, *,
               cluster_network=None, raw=False):
        cluster_network = cluster_network or self._default_cluster_network()
        data = self.create_data(name, namespace, vlan_id, cluster_network)
        path = self.PATH_fmt.format(uid="", ns=namespace, NETWORK_API=self.API_VERSION)
        return self._create(path, json=data, raw=raw)

    def update(self, *args, **kwargs):
        raise NotImplementedError("Update Network is not allowed")

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace, NETWORK_API=self.API_VERSION)
        return self._delete(path, raw=raw)


class SettingManager(BaseManager):
    # get, update
    vlan = "apis/network.{API_VERSION}/clusternetworks/vlan"
    # api-ui-version, backup-target, cluster-registration-url
    PATH_fmt = "apis/{{API_VERSION}}/settings/{name}"
    # "v1/harvesterhci.io.settings/{name}"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(name=name))


class SupportBundlemanager(BaseManager):
    PATH_fmt = ("apis/{{API_VERSION}}/namespaces/harvester-system"
                "/supportbundles/{uid}")
    DL_fmt = "/v1/harvester/supportbundles/{uid}/download"

    def create_data(self, name, description, issue_url):
        data = {
            "apiVersion": "{API_VERSION}",
            "kind": "SupportBundle",
            "metadata": {
                "generateName": f"{name}-",
                "namespace": "harvester-system"
            },
            "spec": {
                "description": description,
                "issueURL": issue_url
            }
        }

        return self._inject_data(data)

    def get(self, uid="", *, raw=False):
        path = self.PATH_fmt.format(uid=uid)
        return self._get(path, raw=raw)

    def create(self, name, description="", issue_url="", *, raw=False):
        data = self.create_data(name, description, issue_url)
        path = self.PATH_fmt.format(uid="")

        return self._create(path, json=data, raw=raw)

    def download(self, uid):
        path = self.DL_fmt.format(uid=uid)
        resp = self._get(path, raw=True)

        return resp.status_code, resp.content

    def update(self, *args, **kwargs):
        raise NotImplementedError("Update Support Bundle is not allowed")

    def delete(self, uid, *, raw=False):
        path = self.PATH_fmt.format(uid=uid)
        return self._delete(path, raw=raw)
