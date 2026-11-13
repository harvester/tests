"""
Terraform component - drives the terraform CLI with the Harvester provider.

Terraform reaches the cluster through the provider, so there is no CRD or
REST implementation to choose from. Each workspace is a directory holding
a main.tf.json file: terraform reads JSON configurations natively, so no
HCL conversion is needed.

Environment:
    TERRAFORM_BIN: terraform binary (default: terraform)
    TF_PROVIDER_VERSION: version constraint of the harvester/harvester
        provider (default: latest release)
    KUBECONFIG: kubeconfig given to the provider (first path of the list)
    TF_CLI_CONFIG_FILE: read by terraform itself, e.g. for a dev_overrides
        block that points to a locally built provider
"""
import json
import os
import shutil
import subprocess
import tempfile

from utility.utility import logging

PROVIDER_SOURCE = "harvester/harvester"
VM_RESOURCE = "harvester_virtualmachine"
VM_NAME_LABEL = "harvesterhci.io/vmName"
HOSTNAME_TOPOLOGY_KEY = "kubernetes.io/hostname"


class Terraform:
    """Terraform component - one directory and configuration per workspace."""

    def __init__(self):
        self.binary = os.getenv("TERRAFORM_BIN", "terraform")
        self.provider_version = os.getenv("TF_PROVIDER_VERSION", "")
        kubeconfig = os.getenv("KUBECONFIG", "~/.kube/config").split(os.pathsep)[0]
        self.kubeconfig = os.path.expanduser(kubeconfig)
        self.workspaces = {}

    def init_workspace(self, workspace):
        provider = {"source": PROVIDER_SOURCE}
        if self.provider_version:
            provider["version"] = self.provider_version
        self.workspaces[workspace] = {
            "dir": tempfile.mkdtemp(prefix=f"tf-{workspace}-"),
            "config": {
                "terraform": {"required_providers": {"harvester": provider}},
                "provider": {"harvester": {"kubeconfig": self.kubeconfig}},
            },
        }
        self._write(workspace)
        self._run(workspace, "init", "-input=false")

    def add_virtual_machine(self, workspace, vm_name, image_id, namespace,
                            cpu, memory, disk_size):
        """Define a VM booting from an image, on the management network."""
        # Terraform rejects an empty "resource" object, so it is only added here
        resources = self._config(workspace).setdefault("resource", {})
        vms = resources.setdefault(VM_RESOURCE, {})
        vms[vm_name] = {
            "name": vm_name,
            "namespace": namespace,
            "cpu": int(cpu),
            "memory": memory,
            "run_strategy": "RerunOnFailure",
            "machine_type": "q35",
            "network_interface": [{"name": "default"}],
            "disk": [{
                "name": "rootdisk",
                "type": "disk",
                "size": disk_size,
                "bus": "virtio",
                "boot_order": 1,
                "image": image_id,
                "auto_delete": True,
            }],
        }
        self._write(workspace)

    def set_required_node_affinity(self, workspace, vm_name, key, value):
        """Only schedule the VM on nodes labelled key=value."""
        self._vm(workspace, vm_name)["node_affinity"] = [{
            "required": [{
                "node_selector_term": [{
                    "match_expressions": [{"key": key, "operator": "In", "values": [value]}],
                }],
            }],
        }]
        self._write(workspace)

    def set_required_pod_anti_affinity(self, workspace, vm_name, other_vm_names):
        """Never schedule the VM on a node running one of the other VMs."""
        self._vm(workspace, vm_name)["pod_anti_affinity"] = [{
            "required": [{
                "topology_key": HOSTNAME_TOPOLOGY_KEY,
                "label_selector": [{
                    "match_expressions": [{
                        "key": VM_NAME_LABEL,
                        "operator": "In",
                        "values": list(other_vm_names),
                    }],
                }],
            }],
        }]
        self._write(workspace)

    def apply(self, workspace):
        self._run(workspace, "apply", "-input=false", "-auto-approve")

    def plan_has_changes(self, workspace):
        """True if a plan of the applied configuration is not empty."""
        result = self._run(workspace, "plan", "-input=false", "-detailed-exitcode",
                           allowed_codes=(0, 2))
        return result.returncode == 2

    def destroy(self, workspace):
        if workspace not in self.workspaces:
            logging(f"No terraform workspace {workspace} to destroy", level="WARNING")
            return
        self._run(workspace, "destroy", "-input=false", "-auto-approve")
        shutil.rmtree(self.workspaces.pop(workspace)["dir"], ignore_errors=True)

    def _config(self, workspace):
        return self.workspaces[workspace]["config"]

    def _vm(self, workspace, vm_name):
        return self._config(workspace)["resource"][VM_RESOURCE][vm_name]

    def _write(self, workspace):
        path = os.path.join(self.workspaces[workspace]["dir"], "main.tf.json")
        with open(path, "w") as f:
            json.dump(self._config(workspace), f, indent=2)

    def _run(self, workspace, *args, allowed_codes=(0,)):
        cmd = [self.binary, *args, "-no-color"]
        logging(f"Running {' '.join(cmd)} in workspace {workspace}")
        result = subprocess.run(cmd, cwd=self.workspaces[workspace]["dir"],
                                capture_output=True, text=True)
        logging(result.stdout, level="DEBUG")
        if result.returncode not in allowed_codes:
            raise AssertionError(
                f"terraform {args[0]} failed in workspace {workspace} "
                f"(exit code {result.returncode}):\n{result.stderr}{result.stdout}")
        return result
