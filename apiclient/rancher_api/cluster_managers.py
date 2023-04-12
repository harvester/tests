from .managers import BaseManager
from .cluster_models import PersistentVolumeClaimSpec

DEFAULT_NAMESPACE = "default"


class PersistentVolumeManager(BaseManager):
    pass


class StorageClassManager(BaseManager):
    PATH_fmt = "v1/storage.k8s.io.storageclasses/{uid}"

    def get(self, name="", *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name), raw=raw)

    def delete(self, name, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name))


class PersistentVolumeClaimManager(BaseManager):
    PATH_fmt = "v1/persistentvolumeclaims/{ns}/{uid}"
    Spec = PersistentVolumeClaimSpec

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.PATH_fmt.format(uid=name, ns=namespace), raw=raw)

    def create(self, name, pvc_spec, namespace=DEFAULT_NAMESPACE, volume=None, *, raw=False):
        if isinstance(pvc_spec, self.Spec):
            pvc_spec = pvc_spec.to_dict(name, namespace, volume)

        path = self.PATH_fmt.format(uid="", ns="").rstrip('/')
        return self._create(path, json=pvc_spec, raw=raw)

    def update(self, name, pvc_spec, namespace=DEFAULT_NAMESPACE, *,
               raw=False, as_json=True, **kwargs):
        if isinstance(pvc_spec, self.Spec):
            pvc_spec = pvc_spec.to_dict(name, namespace, None)

        path = self.PATH_fmt.format(uid=name, ns=namespace)
        return self._update(path, pvc_spec, raw=raw, as_json=as_json, **kwargs)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(self.PATH_fmt.format(uid=name, ns=namespace))
