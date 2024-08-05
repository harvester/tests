from .base import DEFAULT_NAMESPACE, BaseManager


class VolumeSnapshotManager(BaseManager):
    _qs = "?filter=metadata.ownerReferences.kind=PersistentVolumeClaim"
    PATH_fmt = "v1/harvester/snapshot.storage.k8s.io.volumesnapshots/{ns}/{uid}{qs}"

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace)
        return self._delete(path, raw=raw)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace, qs=self._qs)
        return self._get(path, raw=raw)
