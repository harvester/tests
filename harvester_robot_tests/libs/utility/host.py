"""
Command execution on a Harvester node through the Kubernetes API, no SSH needed.
"""
import os
import time

from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from constant import DEFAULT_NAMESPACE
from utility.utility import get_retry_count_and_interval

HOST_POD_IMAGE = os.getenv("WORKLOAD_POD_IMAGE", "busybox:1.36.1")


def exec_command_on_host(node_name, command):
    """Run a command in the host namespaces of node_name via a transient
    privileged hostPID pod (nsenter into PID 1), and return stdout."""
    core_api = client.CoreV1Api()
    pod_name = f"host-probe-{int(time.time() * 1000) % 1000000}"
    body = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "namespace": DEFAULT_NAMESPACE,
            "labels": {"app": "harvester-e2e-host-probe"},
        },
        "spec": {
            "nodeName": node_name,
            "restartPolicy": "Never",
            "hostPID": True,
            "terminationGracePeriodSeconds": 0,
            "tolerations": [{"operator": "Exists"}],
            "containers": [{
                "name": "probe",
                "image": HOST_POD_IMAGE,
                "command": ["sh", "-c", "sleep 300"],
                "securityContext": {"privileged": True,
                                    "runAsUser": 0},
            }],
        },
    }
    core_api.create_namespaced_pod(
        namespace=DEFAULT_NAMESPACE, body=body)
    try:
        retry_count, retry_interval = get_retry_count_and_interval()
        for _ in range(retry_count):
            pod = core_api.read_namespaced_pod(
                name=pod_name, namespace=DEFAULT_NAMESPACE)
            if pod.status and pod.status.phase == "Running":
                break
            time.sleep(retry_interval)
        else:
            raise AssertionError(
                f"Host probe pod on {node_name} did not start")
        resp = stream(
            core_api.connect_get_namespaced_pod_exec,
            pod_name, DEFAULT_NAMESPACE,
            command=["nsenter", "-t", "1", "-m", "-u", "-i", "-n",
                     "--", "sh", "-c", command],
            stderr=True, stdin=False, stdout=True, tty=False,
            _preload_content=False)
        stdout = []
        while resp.is_open():
            resp.update(timeout=5)
            if resp.peek_stdout():
                stdout.append(resp.read_stdout())
            if resp.peek_stderr():
                resp.read_stderr()
        resp.close()
        return "".join(stdout).strip()
    finally:
        try:
            core_api.delete_namespaced_pod(
                name=pod_name, namespace=DEFAULT_NAMESPACE,
                grace_period_seconds=0)
        except ApiException:
            pass
