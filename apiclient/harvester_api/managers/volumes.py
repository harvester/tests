from harvester_api.models.volumes import VolumeSpec
from .base import DEFAULT_NAMESPACE, BaseManager, merge_dict


class VolumeManager(BaseManager):
    # XXX: https://github.com/harvester/harvester/issues/3250
    PATH_fmt = "v1/harvester/persistentvolumeclaims/{ns}{uid}"

    Spec = VolumeSpec

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=f"/{name}", ns=namespace)
        return self._get(path, raw=raw)

    def create(
        self, name, volume_spec, namespace=DEFAULT_NAMESPACE, image_id=None,
        *, raw=False, **kwargs
    ):
        if isinstance(volume_spec, self.Spec):
            volume_spec = volume_spec.to_dict(name, namespace, image_id)

        path = self.PATH_fmt.format(uid="", ns=namespace)
        kws = merge_dict(kwargs, dict(json=volume_spec))
        return self._create(path, raw=raw, **kws)

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
