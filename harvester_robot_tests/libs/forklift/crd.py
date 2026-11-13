"""
Forklift Component: CRD Implementation

Layer 4: Component and its implementation

Reads the ForkliftController / forklift-controller to find the virt-v2v image
Forklift converts guests with, runs that image as a short-lived probe pod to
inspect it, and drives cold migrations through Plan and Migration CRs
(forklift.konveyor.io/v1beta1).
"""

import os
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from crd import get_cr, create_cr, delete_cr, list_cr
from constant import DEFAULT_NAMESPACE
from utility.utility import logging, get_retry_count_and_interval
from .base import Base

FORKLIFT_GROUP = "forklift.konveyor.io"
FORKLIFT_VERSION = "v1beta1"
FORKLIFT_NAMESPACE = os.getenv("FORKLIFT_NAMESPACE", "forklift")
DESTINATION_PROVIDER = os.getenv("FORKLIFT_DESTINATION_PROVIDER", "host")


class CRD(Base):
    """CRD implementation for Forklift operations using the Kubernetes API"""

    def __init__(self):
        super().__init__()
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def _params(self, plural):
        return {"group": FORKLIFT_GROUP, "version": FORKLIFT_VERSION,
                "namespace": FORKLIFT_NAMESPACE, "plural": plural}

    # ---- virt-v2v image ----

    def get_virt_v2v_image(self):
        """Return the virt-v2v image the forklift-controller hands to its
        conversion pods (the VIRT_V2V_IMAGE env, which the operator renders
        from ForkliftController spec.virt_v2v_image_fqin or its default)."""
        deploy = self.apps_api.read_namespaced_deployment(
            name="forklift-controller", namespace=FORKLIFT_NAMESPACE)
        for container in deploy.spec.template.spec.containers:
            for env in container.env or []:
                if env.name == "VIRT_V2V_IMAGE" and env.value:
                    return env.value
        controllers = list_cr(**self._params("forkliftcontrollers"))
        for fc in controllers.get("items", []):
            image = fc.get("spec", {}).get("virt_v2v_image_fqin")
            if image:
                return image
        return None

    def start_image_probe(self, image, pod_name):
        """Run image as an idle pod (entrypoint overridden) and wait until
        it is Running."""
        body = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": pod_name, "namespace": DEFAULT_NAMESPACE,
                         "labels": {"app": "harvester-e2e-virt-v2v-probe"}},
            "spec": {
                "restartPolicy": "Never",
                "terminationGracePeriodSeconds": 0,
                "containers": [{
                    "name": "probe",
                    "image": image,
                    "command": ["sleep", "3600"],
                    "env": [{"name": "LIBGUESTFS_TRACE", "value": "0"},
                            {"name": "LIBGUESTFS_DEBUG", "value": "0"},
                            {"name": "LIBGUESTFS_BACKEND", "value": "direct"}],
                }],
            },
        }
        self.core_api.create_namespaced_pod(namespace=DEFAULT_NAMESPACE, body=body)
        retry_count, retry_interval = get_retry_count_and_interval()
        pod = None
        for _ in range(retry_count):
            pod = self.core_api.read_namespaced_pod(name=pod_name, namespace=DEFAULT_NAMESPACE)
            if pod.status and pod.status.phase == "Running":
                return
            time.sleep(retry_interval)
        raise AssertionError(f"virt-v2v probe pod {pod_name} ({image}) did not start: "
                             f"{pod.status if pod else None}")

    def exec_in_probe(self, pod_name, command, timeout=600):
        """Run a shell command in the probe; return {rc, output} with stdout
        and stderr combined."""
        logging(f"Executing in {pod_name}: {command}", level="DEBUG")
        resp = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            pod_name, DEFAULT_NAMESPACE,
            command=["timeout", str(int(timeout)), "sh", "-c", f"{{ {command} ; }} 2>&1"],
            stderr=True, stdin=False, stdout=True, tty=False,
            _preload_content=False)
        output = []
        resp.run_forever(timeout=int(timeout) + 30)
        output.append(resp.read_stdout() or "")
        output.append(resp.read_stderr() or "")
        rc = resp.returncode
        resp.close()
        return {"rc": rc, "output": "".join(output)}

    def delete_probe(self, pod_name):
        try:
            self.core_api.delete_namespaced_pod(
                name=pod_name, namespace=DEFAULT_NAMESPACE, grace_period_seconds=0)
        except ApiException as e:
            if e.status != 404:
                raise

    # ---- migration ----

    def get_provider(self, name):
        try:
            return get_cr(**self._params("providers"), name=name)
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_plan(self, name, source_provider, storage_map, network_map,
                    vm_name, target_namespace):
        def ref(n):
            return {"name": n, "namespace": FORKLIFT_NAMESPACE}
        body = {
            "apiVersion": f"{FORKLIFT_GROUP}/{FORKLIFT_VERSION}",
            "kind": "Plan",
            "metadata": {"name": name, "namespace": FORKLIFT_NAMESPACE},
            "spec": {
                "warm": False,
                "provider": {"source": ref(source_provider),
                             "destination": ref(DESTINATION_PROVIDER)},
                "map": {"storage": ref(storage_map), "network": ref(network_map)},
                "targetNamespace": target_namespace,
                "vms": [{"name": vm_name}],
            },
        }
        logging(f"Creating Plan {FORKLIFT_NAMESPACE}/{name} for source VM {vm_name}")
        return create_cr(**self._params("plans"), body=body)

    def get_plan(self, name):
        return get_cr(**self._params("plans"), name=name)

    def start_migration(self, name, plan_name):
        body = {
            "apiVersion": f"{FORKLIFT_GROUP}/{FORKLIFT_VERSION}",
            "kind": "Migration",
            "metadata": {"name": name, "namespace": FORKLIFT_NAMESPACE},
            "spec": {"plan": {"name": plan_name, "namespace": FORKLIFT_NAMESPACE}},
        }
        logging(f"Starting Migration {FORKLIFT_NAMESPACE}/{name} of Plan {plan_name}")
        return create_cr(**self._params("migrations"), body=body)

    def get_migration(self, name):
        return get_cr(**self._params("migrations"), name=name)

    def delete_plan_volumes(self, plan_name, namespace):
        """Delete the PVCs Forklift created for a plan (labelled plan=<uid>)."""
        try:
            uid = self.get_plan(plan_name)["metadata"]["uid"]
        except ApiException as e:
            if e.status == 404:
                return
            raise
        pvcs = self.core_api.list_namespaced_persistent_volume_claim(
            namespace=namespace, label_selector=f"plan={uid}").items
        for pvc in pvcs:
            logging(f"Deleting migrated volume {namespace}/{pvc.metadata.name}")
            self.core_api.delete_namespaced_persistent_volume_claim(
                name=pvc.metadata.name, namespace=namespace)

    def _delete(self, plural, name):
        try:
            delete_cr(**self._params(plural), name=name)
        except ApiException as e:
            if e.status != 404:
                raise

    def delete_plan(self, name):
        self._delete("plans", name)

    def delete_migration(self, name):
        self._delete("migrations", name)
