import json

from .base import DEFAULT_NAMESPACE, BaseManager


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
