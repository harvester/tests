import json
from weakref import ref
from pathlib import Path
from collections.abc import Mapping

from pkg_resources import parse_version

from .models import (
    VolumeSpec, VMSpec, BaseSettingSpec, BackupTargetSpec, RestoreSpec, StorageNetworkSpec
)

DEFAULT_NAMESPACE = "default"
DEFAULT_HARVESTER_NAMESPACE = "harvester-system"
DEFAULT_LONGHORN_NAMESPACE = "longhorn-system"

DEFAULT_STORAGE_CLASS_ANNOTATION = "storageclass.kubernetes.io/is-default-class"


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
            if "json" in resp.headers.get('Content-Type', ""):
                rval = resp.json()
            else:
                rval = resp.text
            return resp.status_code, rval
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

    def _patch(self, path, *, raw=False, **kwargs):
        return self._delegate("_patch", path, raw=raw, **kwargs)

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

    def maintenance_mode(self, name, enable=True, force=False):
        action = "enable" if enable else "disable"
        params = dict(action=f"{action}MaintenanceMode")
        payload = dict(force=str(force).lower())
        return self._create(self.PATH_fmt.format(uid=name), params=params, json=payload)


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
        file = Path(filepath).expanduser()

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
    # XXX: https://github.com/harvester/harvester/issues/3250
    PATH_fmt = "v1/harvester/persistentvolumeclaims/{ns}{uid}"

    Spec = VolumeSpec

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._get(path, raw=raw)

    def create(self, name, volume_spec, namespace=DEFAULT_NAMESPACE, image_id=None, *, raw=False):
        if isinstance(volume_spec, self.Spec):
            volume_spec = volume_spec.to_dict(name, namespace, image_id)

        path = self.PATH_fmt.format(uid="", ns=namespace)
        return self._create(path, json=volume_spec, raw=raw)

    def update(self, name, volume_spec, namespace=DEFAULT_NAMESPACE, *,
               raw=False, as_json=True, **kwargs):
        if isinstance(volume_spec, self.Spec):
            volume_spec = volume_spec.to_dict(name, namespace)

        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._update(path, volume_spec, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._delete(path, raw=raw)

    def export(self, name, image_name, storage_class, namespace=DEFAULT_NAMESPACE, *, raw=False):
        export_spec = {"displayName": image_name, "namespace": namespace,
                       "storageClassName": storage_class}
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="export")
        return self._create(path, params=params, json=export_spec, raw=raw)


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
    BACKUP_fmt = "v1/harvester/harvesterhci.io.virtualmachinebackups/{ns}/{uid}"
    RESTORE_fmt = "v1/harvester/harvesterhci.io.virtualmachinerestores/{ns}"

    RestoreSpec = RestoreSpec

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False, **kwargs):
        path = self.BACKUP_fmt.format(uid=name, ns=namespace)
        return self._get(path, raw=raw, **kwargs)

    def create(self, name, restore_spec, namespace=DEFAULT_NAMESPACE, *, raw=False, **kwargs):
        _, data = self.get(name, namespace)
        old_vm = data['spec']['source']['name']
        spec = restore_spec.to_dict(name, namespace, old_vm)
        path = self.RESTORE_fmt.format(ns=restore_spec.namespace or namespace)
        return self._create(path, json=spec, raw=raw, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False, **kwargs):
        path = self.BACKUP_fmt.format(uid=name, ns=namespace)
        return self._delete(path, raw=raw, **kwargs)

    restore = create  # alias


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

    def _bridge_name(self, cluster_network=None):
        if cluster_network is not None:
            return f"{cluster_network}-br"
        if self.api.cluster_version >= parse_version("v1.1.0"):
            return "mgmt-br"
        else:
            return "harvester-br0"

    def create_data(self, name, namespace, vlan_id, bridge_name, mode="auto", cidr="", gateway=""):
        data = {
            "apiVersion": self.API_VERSION,
            "kind": self._KIND,
            "metadata": {
                "annotations": {
                    "network.harvesterhci.io/route": json.dumps({
                        "mode": mode,
                        "serverIPAddr": "",
                        "cidr": cidr,
                        "gateway": gateway
                    })
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
               cluster_network=None, mode="auto", cidr="", gateway="", raw=False):
        data = self.create_data(name, namespace, vlan_id, self._bridge_name(cluster_network),
                                mode=mode, cidr=cidr, gateway=gateway)
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
    Spec = BaseSettingSpec
    BackupTargetSpec = BackupTargetSpec
    StorageNetworkSpec = StorageNetworkSpec

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(name=name))

    def update(self, name, spec, *, raw=False, as_json=True, **kwargs):
        path = self.PATH_fmt.format(name=name)
        _, node = self.get(name)
        if isinstance(spec, BaseSettingSpec):
            spec = spec.to_dict(node)
        if isinstance(spec, Mapping) and as_json:
            spec = merge_dict(spec, node)
        return self._update(path, spec, raw=raw, as_json=as_json, **kwargs)

    def backup_target_test_connection(self, *, raw=False):
        path = "/v1/harvester/backuptarget/healthz"
        return self._get(path, raw=raw)


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


class ClusterNetworkManager(BaseManager):
    PATH_fmt = "apis/network.{{API_VERSION}}/clusternetworks/{uid}"
    CONFIG_fmt = "apis/network.{{API_VERSION}}/vlanconfigs/{uid}"
    _default_bond_mode = "active-backup"

    def create_data(self, name, description="", labels=None, annotations=None):
        data = {
            "apiVersion": "network.{API_VERSION}",
            "kind": "ClusterNetwork",
            "metadata": {
                "annotations": {
                    "field.cattle.io/description": description
                },
                "labels": labels or dict(),
                "name": name
            }

        }

        if annotations is not None:
            data['metadata']['annotations'].update(annotations)

        return self._inject_data(data)

    def create_config_data(self, name, clusternetwork, *nics,
                           bond_mode=None, hostname=None, miimon=None, mtu=None):
        data = {
            "apiVersion": "network.{API_VERSION}",
            "kind": "VlanConfig",
            "metadata": {
                "name": name
            },
            "spec": {
                "clusterNetwork": clusternetwork,
                "uplink": {
                    "bondOptions": {
                        "mode": bond_mode or self._default_bond_mode,
                    },
                    "nics": nics
                }
            }
        }

        if hostname is not None:
            data['spec']['nodeSelector']["kubernetes.io/hostname"] = hostname

        if miimon is not None:
            data['spec']['uplink']['bondOptions']['miimon'] = miimon

        if mtu is not None:
            data['spec']['uplink']["linkAttributes"] = {
                "mtu": mtu
            }

        return self._inject_data(data)

    def get(self, name="", raw=False):
        path = self.PATH_fmt.format(uid=name)
        return self._get(path, raw=raw)

    def create(self, name, description="", labels=None, annotations=None, *, raw=False):
        data = self.create_data(name, description, labels, annotations)
        path = self.PATH_fmt.format(uid="")
        return self._create(path, json=data, raw=raw)

    def update(self, name, data, *, raw=False, as_json=True, **kwargs):
        path = self.PATH_fmt.format(uid=name)
        if isinstance(data, Mapping) and as_json:
            _, node = self.get(name)
            data = merge_dict(data, node)
        return self._update(path, data, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, *, raw=False):
        path = self.PATH_fmt.format(uid=name)
        return self._delete(path, raw=raw)

    def get_config(self, name="", raw=False):
        path = self.CONFIG_fmt.format(uid=name)
        return self._get(path, raw=raw)

    def create_config(self, name, clusternetwork, *nics,
                      bond_mode=None, hostname=None, miimon=None, mtu=None, raw=False):
        data = self.create_config_data(name, clusternetwork, *nics, bond_mode=bond_mode,
                                       hostname=hostname, miimon=miimon, mtu=mtu)
        path = self.CONFIG_fmt.format(uid=name)
        return self._create(path, json=data, raw=raw)

    def update_config(self, name, data, *, raw=False, as_json=True, **kwargs):
        path = self.CONFIG_fmt.format(uid=name)
        if isinstance(data, Mapping) and as_json:
            _, node = self.get_config(name)
            data = merge_dict(data, node)
        return self._update(path, data, raw=raw, as_json=as_json, **kwargs)

    def delete_config(self, name, *, raw=False):
        path = self.CONFIG_fmt.format(uid=name)
        return self._delete(path, raw=raw)


class VirtualMachineManager(BaseManager):
    API_VERSION = "kubevirt.io/v1"

    # operators: start, restart, stop, migrate, pause, unpause, softreboot
    PATH_fmt = "v1/harvester/kubevirt.io.virtualmachines/{ns}{uid}"
    # guestinfo, network
    VMI_fmt = "v1/harvester/kubevirt.io.virtualmachineinstances/{ns}/{uid}"
    # operators: guestosinfo, console(ws), vnc(ws)
    VMIOP_fmt = "apis/subresources.{VM_API}/namespaces/{ns}/virtualmachineinstances/{uid}/{op}"

    Spec = VMSpec

    def download_virtctl(self, *, raw=False, **kwargs):
        code, info = self._get(f"apis/subresources.{self.VM_API}/v1/version")
        version, platform = info['gitVersion'], info['platform']
        resp = self.api.session.get("https://github.com/kubevirt/kubevirt/releases/download/"
                                    f"{version}/virtctl-{version}-{platform}", **kwargs)
        if raw:
            return resp
        else:
            return resp.status_code, resp.content

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False, **kwargs):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._get(path, raw=raw, **kwargs)

    def get_status(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False, **kwargs):
        path = self.VMI_fmt.format(uid=name, ns=namespace)
        return self._get(path, raw=raw, **kwargs)

    def create(self, name, vm_spec, namespace=DEFAULT_NAMESPACE, *, raw=False):
        if isinstance(vm_spec, self.Spec):
            vm_spec = vm_spec.to_dict(name, namespace)
        path = self.PATH_fmt.format(uid="", ns=namespace)
        return self._create(path, json=vm_spec, raw=raw)

    def update(self, name, vm_spec, namespace=DEFAULT_NAMESPACE, *,
               raw=False, as_json=True, **kwargs):
        if isinstance(vm_spec, self.Spec):
            vm_spec = vm_spec.to_dict(name, namespace)
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._update(path, vm_spec, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._delete(path, raw=raw)

    def clone(self, name, new_vm_name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="clone")
        return self._create(path, raw=raw, params=params, json=dict(targetVm=new_vm_name))

    def backup(self, name, backup_name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="backup")
        return self._create(path, raw=raw, params=params, json=dict(name=backup_name))

    def start(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="start")
        return self._create(path, raw=raw, params=params)

    def restart(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="restart")
        return self._create(path, raw=raw, params=params)

    def stop(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="stop")
        return self._create(path, raw=raw, params=params)

    def migrate(self, name, target_node, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="migrate")
        return self._create(path, raw=raw, params=params, json=dict(nodeName=target_node))

    def abort_migrate(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="abortMigration")
        return self._create(path, raw=raw, params=params)

    def pause(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="pause")
        return self._create(path, raw=raw, params=params)

    def unpause(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="unpause")
        return self._create(path, raw=raw, params=params)

    def softreboot(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        params = dict(action="softreboot")
        return self._create(path, raw=raw, params=params)


class StorageClassManager(BaseManager):
    API_VERSION = "storage.k8s.io"

    CREATE_PATH_fmt = "v1/harvester/{SC_API}.storageclasses"

    PATH_fmt = "/apis/{SC_API}/v1/storageclasses/{name}"

    def get(self, name="", *, raw=False, **kwargs):
        path = self.PATH_fmt.format(SC_API=self.API_VERSION, name=name)
        return self._get(path, raw=raw, **kwargs)

    def create_data(self, name, replicas):
        data = {
            "type": f"{self.API_VERSION}",
            "metadata": {
                "name": name
            },
            "parameters": {
                "numberOfReplicas": f"{replicas}",
                "staleReplicaTimeout": "30",
                "migratable": "true"
            },
            "provisioner": "driver.longhorn.io",
            "allowVolumeExpansion": True,
            "reclaimPolicy": "Delete",
            "volumeBindingMode": "Immediate"
        }

        return data

    def create(self, name, replicas=3, *, raw=False):
        path = self.CREATE_PATH_fmt.format(SC_API=self.API_VERSION)
        data = self.create_data(name, replicas)
        return self._create(path, json=data, raw=raw)

    def set_default(self, name, *, raw=False):
        code, resp = self.get()

        if code == 200 and len(resp['items']):
            for sc in resp['items']:
                if sc['metadata'].get('annotations', {}).get(
                   DEFAULT_STORAGE_CLASS_ANNOTATION) == 'true':

                    if sc['metadata']['name'] == name:
                        return (200, sc)

                    # reset old default storage class
                    path = self.PATH_fmt.format(name=sc['metadata']['name'],
                                                SC_API=self.API_VERSION)
                    resp = self._patch(path, json={
                        "metadata": {
                            "annotations": {
                                "storageclass.kubernetes.io/is-default-class": "false",
                                "storageclass.beta.kubernetes.io/is-default-class": "false"
                            }
                        }
                    }, raw=raw)

                    break

        path = self.PATH_fmt.format(name=name, SC_API=self.API_VERSION)
        return self._patch(path, json={
            "metadata": {
                "annotations": {
                    "storageclass.kubernetes.io/is-default-class": "true",
                    "storageclass.beta.kubernetes.io/is-default-class": "true"
                }
            }
        }, raw=raw)

    def delete(self, name, *, raw=False):
        path = self.PATH_fmt.format(name=name, SC_API=self.API_VERSION)
        return self._delete(path, raw=raw)


class VersionManager(BaseManager):
    PATH_fmt = "apis/harvesterhci.io/v1beta1/namespaces/{namespace}/versions/{name}"

    API_PATH_fmt = "v1/harvester/harvesterhci.io.versions/{namespace}{name}"

    def get(self, name="", namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False, **kwargs):
        path = self.PATH_fmt.format(name=name, namespace=namespace)
        return self._get(path, raw=raw, **kwargs)

    def create_data(self, name, url, checksum):
        data = {
            "metadata": {
                "name": name,
                "namespace": "harvester-system"
            },
            "spec": {
                "isoChecksum": checksum,
                "isoURL": url
            }
        }
        return data

    def create(self, name, url, checksum, namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False):
        data = self.create_data(name, url, checksum)
        path = self.API_PATH_fmt.format(name="", namespace=namespace)
        return self._create(path, json=data, raw=raw)

    def delete(self, name, namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False):
        path = self.API_PATH_fmt.format(name=f"/{name}", namespace=namespace)
        return self._delete(path, raw=raw)


class UpgradeManager(BaseManager):
    PATH_fmt = "apis/harvesterhci.io/v1beta1/namespaces/{namespace}/upgrades/{name}"

    CREATE_PATH = "v1/harvester/harvesterhci.io.upgrades"
    API_PATH_fmt = "v1/harvester/harvesterhci.io.upgrades/{namespace}{name}"

    def create_data(self, version_name, namespace=DEFAULT_HARVESTER_NAMESPACE):
        data = {
            "type": "harvesterhci.io.upgrade",
            "metadata": {
                "generateName": "hvst-upgrade-",
                "namespace": namespace
            },
            "spec": {
                "version": version_name
            }
        }
        return data

    def create(self, version_name, namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False):
        data = self.create_data(version_name)
        path = self.API_PATH_fmt.format(name="", namespace=namespace)
        return self._create(path, json=data, raw=raw)

    def get(self, name="", namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False, **kwargs):
        path = self.PATH_fmt.format(name=name, namespace=namespace)
        return self._get(path, raw=raw, **kwargs)

    def delete(self, name, namespace=DEFAULT_HARVESTER_NAMESPACE, *, raw=False):
        path = self.API_PATH_fmt.format(name=f"/{name}", namespace=f"{namespace}")
        return self._delete(path, raw=raw)


class LonghornReplicaManager(BaseManager):
    API_VERSION = "longhorn.io/v1beta2"
    PATH_fmt = "apis/{API_VERSION}/namespaces/{namespace}/replicas/{name}"

    API_PATH_fmt = "v1/harvester/longhorn.io.replicas/{namespace}{name}"

    def get(self, name="", namespace=DEFAULT_LONGHORN_NAMESPACE, *, raw=False, **kwargs):
        path = self.PATH_fmt.format(API_VERSION=self.API_VERSION, name=name, namespace=namespace)
        return self._get(path, raw=raw, **kwargs)

    def delete(self, name="", namespace=DEFAULT_LONGHORN_NAMESPACE, *, raw=False):
        path = self.API_PATH_fmt.format(name=f"/{name}", namespace=namespace)
        return self._delete(path, raw=raw)


class LonghornVolumeManager(BaseManager):
    API_VERSION = "longhorn.io/v1beta2"
    PATH_fmt = "apis/{API_VERSION}/namespaces/{namespace}/volumes/{name}"

    API_PATH_fmt = "v1/harvester/longhorn.io.volumes/{namespace}{name}"

    def get(self, name="", namespace=DEFAULT_LONGHORN_NAMESPACE, *, raw=False, **kwargs):
        path = self.PATH_fmt.format(API_VERSION=self.API_VERSION, name=name, namespace=namespace)
        return self._get(path, raw=raw, **kwargs)
