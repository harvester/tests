from urllib.parse import urljoin

from .cluster_managers import (StorageClassManager, PersistentVolumeClaimManager)


class ClusterExploreAPI:
    def __init__(self, endpoint, session, cluster_id):
        self.endpoint = endpoint
        self.cluster_id = cluster_id
        self.session = session

        # Storage
        self.storageclasses = self.scs = StorageClassManager(self)
        self.persistentvolumeclaims = self.pvcs = PersistentVolumeClaimManager(self)

    def _get(self, path, **kwargs):
        url = urljoin(self.endpoint, f"k8s/clusters/{self.cluster_id}/{path}")
        return self.session.get(url, **kwargs)

    def _post(self, path, **kwargs):
        url = urljoin(self.endpoint, f"k8s/clusters/{self.cluster_id}/{path}")
        return self.session.post(url, **kwargs)

    def _put(self, path, **kwargs):
        url = urljoin(self.endpoint, f"k8s/clusters/{self.cluster_id}/{path}")
        return self.session.put(url, **kwargs)

    def _delete(self, path, **kwargs):
        url = urljoin(self.endpoint, f"k8s/clusters/{self.cluster_id}/{path}")
        return self.session.delete(url, **kwargs)
