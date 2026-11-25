"""
List API Keywords - creates ListAPI() instance and delegates - NO direct API calls!
"""
import os
import sys

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from list_api.list_api import ListAPI # noqa E402


class list_api_keywords:
    """List API keyword wrapper - creates ListAPI component and delegates"""

    def __init__(self):
        self.list_api = ListAPI()

    def query(self, path, retries=True, **params):
        """GET a list of the Harvester API. Returns {code, ids, count, body}"""
        return self.list_api.query(path, retries, **params)

    def get_schema(self, type_id):
        """Return (code, schema) of a type of /v1/harvester"""
        return self.list_api.schema(type_id)

    def get_k8s_ids(self, path):
        """Sorted ids (namespace/name or name) of a list of the Kubernetes API"""
        return self.list_api.k8s_ids(path)

    def get_k8s_ids_of_schema(self, schema):
        """Sorted ids of the Kubernetes list of the resource of a schema"""
        return self.list_api.k8s_collection_ids(schema)

    def create_namespace(self, name, labels=None):
        """Create a namespace through the Harvester API"""
        self.list_api.create_namespace(name, labels)

    def delete_namespace(self, name):
        """Delete a namespace through the Harvester API, returns the code"""
        return self.list_api.delete_namespace(name)

    def update_namespace_labels(self, name, labels):
        """Merge labels into a namespace through the Harvester API"""
        self.list_api.update_namespace_labels(name, labels)

    def get_namespace(self, name):
        """Return (code, namespace) of the Harvester API"""
        return self.list_api.get_namespace(name)

    def delete_vm(self, vm_name, namespace, removed_disks=None):
        """Delete a VM through the VM store of the Harvester API"""
        self.list_api.delete_vm(vm_name, namespace, removed_disks)

    def open_subscription(self, resource_type, **options):
        """Subscribe to the events of a type over /v1/harvester/subscribe"""
        self.list_api.open_subscription(resource_type, **options)

    def close_subscription(self):
        """Close the subscription"""
        self.list_api.close_subscription()

    def next_event(self, name, obj_id=None, timeout=30):
        """Wait for an event of an object, returns the message"""
        return self.list_api.next_event(name, obj_id, timeout)

    def receive_events(self, seconds):
        """All events that arrive in seconds, as (name, id) pairs"""
        return self.list_api.receive_events(seconds)
