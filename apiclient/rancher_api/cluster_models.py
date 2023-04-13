from copy import deepcopy
from enum import Flag, auto
from operator import or_, xor
from functools import reduce


class AccessModes(Flag):
    ReadWriteOnce = auto()
    ReadWriteMany = auto()
    ReadOnlyMany = auto()

    def __iter__(self):
        # Only for Python version < 3.11
        # ref: https://github.com/python/cpython/blob/e643412ef443b7a6847833f1e140b567622ac383/Lib/enum.py#L1361 # noqa
        num = self._value_
        while num:
            val = num & (~num + 1)
            yield self._value2member_map_.get(val)
            num ^= val


class PersistentVolumeClaimSpec:
    _data = None

    def __init__(self, size, storage_cls="", description="", *, labels=None, annotations=None):
        self.access_modes = AccessModes.ReadWriteOnce

        self.size = size
        self.storage_cls = storage_cls
        self.description = description
        self.labels = labels
        self.annotations = annotations

    @property
    def mode_rwo(self):
        return bool(self.access_modes & AccessModes.ReadWriteOnce)

    @mode_rwo.setter
    def mode_rwo(self, enable):
        op = or_ if enable else xor
        self.access_modes = op(self.access_modes, AccessModes.ReadWriteOnce)

    @property
    def mode_rwm(self):
        return bool(self.access_modes & AccessModes.ReadWriteMany)

    @mode_rwm.setter
    def mode_rwm(self, enable):
        op = or_ if enable else xor
        self.access_modes = op(self.access_modes, AccessModes.ReadWriteMany)

    @property
    def mode_rom(self):
        return bool(self.access_modes & AccessModes.ReadOnlyMany)

    @mode_rom.setter
    def mode_rom(self, enable):
        op = or_ if enable else xor
        self.access_modes = op(self.access_modes, AccessModes.ReadOnlyMany)

    def to_dict(self, name, namespace, volume=None):
        labels = self.labels or dict()
        annotations = self.annotations or dict()
        size = f"{self.size}Gi" if isinstance(self.size, (int, float)) else self.size
        modes = [m.name for m in self.access_modes]
        data = {
            "type": "persistentvolumeclaim",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations,
                "labels": labels
            },
            "spec": {
                "accessModes": modes,
                "volumeName": volume or (self._data and self._data['spec'].get('volumeName')),
                "resources": {
                    "requests": dict(storage=size)
                }
            },
            "accessModes": modes
        }

        if self.storage_cls or volume:
            data['spec']['storageClassName'] = "" if volume else self.storage_cls

        if self.description:
            data['metadata']['annotations']['field.cattle.io/description'] = self.description

        if self._data:
            self._data['metadata'].update(data['metadata'])
            self._data['spec'].update(data['spec'])
            return deepcopy(self._data)

        return deepcopy(data)

    @classmethod
    def from_dict(cls, data):
        spec, metadata = data['spec'], data['metadata']
        annotations = metadata.get('annotations', {})
        size = spec['resources']['requests']['storage']
        storage_cls = spec.get('storageClassName')

        obj = cls(size, storage_cls, annotations.get("field.cattle.io/description"))
        obj.annotations = annotations
        obj.labels = metadata.get('labels', {})
        obj.access_modes = reduce(or_, (getattr(AccessModes, m) for m in spec['accessModes']))
        obj._data = data

        return obj
