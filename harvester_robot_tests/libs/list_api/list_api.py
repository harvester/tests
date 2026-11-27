""" List API Component

Layer 4: Component. REST only: the lists of the Harvester API (filter, sort
and pages, served by the SQL cache of Steve), the matching lists of the
Kubernetes API, the watch over /v1/harvester/subscribe, and the calls that
have to go through a store of the Harvester API.
"""

import json
import ssl
from datetime import datetime, timedelta
from time import sleep
from urllib.parse import urlparse

import websocket

from utility.utility import get_harvester_api_client, get_retry_count_and_interval


class ListAPI:

    def __init__(self):
        self.ws = None
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    @property
    def api(self):
        return get_harvester_api_client()

    def query(self, path, retries=True, **params):
        """GET `path` with `params` as query; returns code, ids, count and the body.

        retries=False returns an expected 4xx/5xx at once instead of retrying a 500.
        """
        if not retries:
            self.api.set_retries(1, total=0)
        try:
            code, data = self.api.get(path, params=params)
        finally:
            if not retries:
                self.api.set_retries()
        body = data if isinstance(data, dict) else {}
        return {
            "code": code,
            "ids": [item["id"] for item in body.get("data", [])],
            "count": body.get("count"),
            "body": data,
        }

    def k8s_ids(self, path):
        """Sorted ids (namespace/name or name) of a list of the Kubernetes API"""
        code, data = self.api.get(path)
        assert code == 200, (code, data)
        return sorted(
            "/".join(filter(None, (i["metadata"].get("namespace"), i["metadata"]["name"])))
            for i in data["items"])

    def k8s_collection_ids(self, schema):
        attrs = schema["attributes"]
        group = attrs.get("group")
        prefix = f"apis/{group}" if group else "api"
        return self.k8s_ids(f"{prefix}/{attrs['version']}/{attrs['resource']}")

    def schema(self, type_id):
        return self.api.get(f"v1/harvester/schemas/{type_id}")

    def create_namespace(self, name, labels=None):
        """Through the Harvester API, the namespace store under test"""
        code, data = self.api.namespaces.create(name, labels=labels)
        assert code == 201, (code, data)

    def delete_namespace(self, name):
        return self.api.namespaces.delete(name)[0]

    def update_namespace_labels(self, name, labels):
        for _ in range(self.retry_count):
            code, data = self.api.namespaces.update(name, dict(labels=labels))
            if code != 409:
                break
            sleep(self.retry_interval)
        assert code == 200, (code, data)

    def get_namespace(self, name):
        return self.api.namespaces.get(name)

    def delete_vm(self, vm_name, namespace, removed_disks=None):
        """Through the VM store of the Harvester API, which removes the PVCs of removed_disks"""
        params = {"removedDisks": removed_disks} if removed_disks else None
        # A client retry after a 500 would answer 404 for a VM that is already gone
        self.api.set_retries(1, total=0)
        try:
            code, data = self.api.vms.delete(vm_name, namespace, params=params)
        finally:
            self.api.set_retries()
        # 204: the VM is gone at once (no finalizer yet), also a successful delete
        assert code in (200, 204), (code, data)

    def open_subscription(self, resource_type, **options):
        self.close_subscription()
        host = urlparse(self.api.endpoint).netloc
        self.ws = websocket.create_connection(
            f"wss://{host}/v1/harvester/subscribe",
            header=[f"Authorization: {self.api.session.headers['Authorization']}"],
            origin=f"https://{host}",
            sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
            timeout=10)
        self.ws.send(json.dumps(dict(resourceType=resource_type, **options)))

    def close_subscription(self):
        if self.ws:
            self.ws.close()
            self.ws = None

    def _recv(self, timeout):
        self.ws.settimeout(timeout)
        try:
            return json.loads(self.ws.recv())
        except (websocket.WebSocketTimeoutException, ValueError):
            return None

    def next_event(self, name, obj_id=None, timeout=30):
        """Wait for an event; other events are skipped. Returns the message."""
        end = datetime.now() + timedelta(seconds=float(timeout))
        seen = []
        while end > datetime.now():
            message = self._recv(5)
            if message is None:
                continue
            data = message.get("data") or {}
            if message.get("name") == name and obj_id in (None, data.get("id")):
                return message
            seen.append(f"{message.get('name')} {data.get('id')}")
        raise AssertionError(f"Timeout while waiting for {name}, skipped events: {seen}")

    def receive_events(self, seconds):
        """All events that arrive in `seconds`, as (name, id) pairs"""
        end = datetime.now() + timedelta(seconds=float(seconds))
        events = []
        while end > datetime.now():
            message = self._recv(1)
            if message is not None:
                events.append((message.get("name"), (message.get("data") or {}).get("id")))
        return events
