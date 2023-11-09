from .base import DEFAULT_NAMESPACE, BaseManager


class VolumeSnapshotManager(BaseManager):
    PATH_fmt = "v1/harvester/snapshot.storage.k8s.io.volumesnapshots/{ns}/{uid}"

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace)
        return self._delete(path, raw=raw)

    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        path = self.PATH_fmt.format(uid=name, ns=namespace)
        return self._get(path, raw=raw)
