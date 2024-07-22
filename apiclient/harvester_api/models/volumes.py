from copy import deepcopy


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
            annotations.update({"harvesterhci.io/imageId": image_id})
            self.storage_cls = f"longhorn-{image_id.split('/')[1]}"
        if self.description is not None:
            annotations.update({"field.cattle.io/description": self.description})
        if self.storage_cls is not None:
            data['spec']['storageClassName'] = self.storage_cls

        if self._data:
            self._data['metadata'].update(data['metadata'])
            self._data['spec'].update(data['spec'])
            return deepcopy(self._data)

        return deepcopy(data)

    @classmethod
    def from_dict(cls, data):
        spec, metadata = data.get('spec', {}), data.get('metadata', {})
        annotations = metadata.get('annotations')
        size = spec['resources']['requests']['storage']
        storage_cls = spec.get('storageClassName')

        obj = cls(size, storage_cls, annotations=annotations)
        obj._data = data

        return obj
