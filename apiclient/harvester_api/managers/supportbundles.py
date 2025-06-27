from .base import BaseManager


class SupportBundleManager(BaseManager):
    PATH_fmt = ("apis/{{API_VERSION}}/namespaces/harvester-system"
                "/supportbundles/{uid}")
    DL_fmt = "/v1/harvester/supportbundles/{uid}/download"

    def create_data(
        self, name, description, issue_url,
        timeout, node_timeout, expiration, extra_collection_namespaces,
    ):
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

        if timeout is not None:
            data['spec']['timeout'] = timeout
        if node_timeout is not None:
            data['spec']['nodeTimeout'] = node_timeout
        if expiration is not None:
            data['spec']['expiration'] = expiration
        if extra_collection_namespaces is not None:
            data['spec']['extraCollectionNamespaces'] = extra_collection_namespaces

        return self._inject_data(data)

    def get(self, uid="", *, raw=False):
        path = self.PATH_fmt.format(uid=uid)
        return self._get(path, raw=raw)

    def create(self, name, description="", issue_url="",
               timeout=None, node_timeout=None, expiration=None,
               extra_collection_namespaces=None, *, raw=False):
        data = self.create_data(
            name, description,
            issue_url, timeout, node_timeout,
            expiration, extra_collection_namespaces
        )
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
