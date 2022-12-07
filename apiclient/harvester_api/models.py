class VMSpec:
    # ref: https://kubevirt.io/api-reference/master/definitions.html#_v1_virtualmachineinstancespec
    # defaults
    sockets = threads = 1
    run_strategy = "RerunOnFailure",
    eviction_strategy = "LiveMigrate"
    acpi = True
    # cpu, mem, volumes, networks
    # VolumeClaimTemplates
    # affinity

    def __init__(self, cpu=1, mem=1):
        pass

    def add_image(self, name, size, bus="virtio", type="disk"):
        pass

    def add_container(self, name, image_name, bus="virtio", type="disk"):
        pass

    def add_volume(self):
        pass

    def add_network(self):
        pass

    def to_dict(self, name, hostname=None):
        acpi = dict(enabled=self.acpi)
        machine = dict()
        cpu = dict(sockets=self.sockets, thread=self.threads)
        devices = dict()
        resources = dict()
        networks = []
        volumes = []

        return {
            "runStrategy": self.run_strategy,
            "template": {
                "metadata": {
                    "labels": {
                        "harvesterhci.io/vmName": name
                    }
                },
                "spec": {
                    "evictionStrategy": self.eviction_strategy,
                    "hostname": hostname or name,
                    "networks": networks,
                    "volumes": volumes,
                    "domain": {
                        "machine": machine,
                        "cpu": cpu,
                        "devices": devices,
                        "resources": resources,
                        "features": dict(acpi=acpi)
                    }
                }
            }
        }


class VolumeSpec:
    volume_mode = "Block"
    _data = None

    def __init__(self, size, storage_cls=None, description=None, annotations=None):
        self.access_modes = ["ReadWriteMany"]

        self.size = size
        self.storage_cls = storage_cls
        self.description = description
        self.annotations = annotations

    def to_dict(self, name, namespace, image_id=None):
        annotations = self.annotations or dict()
        size = f"{self.size}Gi" if isinstance(self.size, (int, float)) else self.size
        data = {
            "type": "persistentvolumeclaim",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations
            },
            "spec": {
                "accessModes": self.access_modes,
                "resources": {
                    "requests": dict(storage=size)
                },
                "volumeMode": self.volume_mode
            }
        }

        if image_id is not None:
            annotations.update({"harvesterhci.io/imageId": self.image_id})
        if self.description is not None:
            annotations.update({"field.cattle.io/description": self.description})
        if self.storage_cls is not None:
            data['spec']['storageClassName'] = self.storage_cls

        if self._data:
            self._data['metadata'].update(data['metadata'])
            self._data['spec'].update(data['spec'])
            return self._data

        return data

    @classmethod
    def from_dict(cls, data):
        spec, metadata = data.get('spec', {}), data.get('metadata', {})
        annotations = metadata.get('annotations')
        size = spec['resources']['requests']['storage']
        storage_cls = spec.get('storageClassName')

        obj = cls(size, storage_cls, annotations.get("field.cattle.io/description"))
        obj.annotations = annotations
        obj._data = data

        return obj
