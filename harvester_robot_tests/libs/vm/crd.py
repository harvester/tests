"""
VM CRD Implementation
"""
import ast
import json
import re
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from crd import get_cr, create_cr, delete_cr, list_cr, wait_for_cr_deleted, patch_cr
from constant import (
    KUBEVIRT_API_GROUP, KUBEVIRT_API_VERSION,
    VIRTUALMACHINE_PLURAL, VIRTUALMACHINEINSTANCE_PLURAL,
    DEFAULT_NAMESPACE, LABEL_TEST, LABEL_TEST_VALUE,
    DEFAULT_TIMEOUT, DEFAULT_TIMEOUT_SHORT,
    VM_STATE_RUNNING, VM_STATE_STOPPED,
    RUN_STRATEGY_RERUN_ON_FAILURE,
    DATA_FILE,
    DEFAULT_USER_DATA,
)
from utility.utility import logging, get_retry_count_and_interval
from vm.base import Base


def _parse_virsh_output(raw):
    """Parse virsh qemu-agent-command output into a Python dict.
    """
    # First pass: find the first valid JSON object in the raw string.
    decoder = json.JSONDecoder()
    idx = 0
    while idx != -1:
        idx = raw.find("{", idx)
        if idx == -1:
            break
        try:
            obj, _ = decoder.raw_decode(raw, idx)
            return obj
        except json.JSONDecodeError:
            idx += 1

    # Fallback: some kubernetes client versions return str(dict) which uses
    # single-quoted Python syntax.  ast.literal_eval handles this safely.
    try:
        result = ast.literal_eval(raw.strip())
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass

    raise ValueError(f"No JSON object found in stream output: {raw!r}")


class CRD(Base):
    """
    VM CRD implementation - uses Kubernetes Custom Resources
    """

    def __init__(self):
        """Initialize CRD client."""
        self.obj_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.storage_api = client.StorageV1Api()
        self.retry_count, self.retry_interval = (
            get_retry_count_and_interval()
        )

    def create(self, vm_name, cpu, memory, image_id, **kwargs):
        """Create a VM using CRD"""
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)

        try:
            logging(f"Creating VirtualMachine {namespace}/{vm_name}")
            self._create_virtual_machine(
                vm_name, cpu, memory, image_id, namespace, **kwargs
            )

            # Wait for VM to be created
            self.wait_for_vm_created(vm_name, namespace)

            logging(f"VM {namespace}/{vm_name} created successfully")

            return {'metadata': {'name': vm_name, 'namespace': namespace}}

        except Exception as e:
            logging(f"Failed to create VM {vm_name}: {e}")
            raise

    def _create_virtual_machine(
            self, vm_name, cpu, memory, image_id, namespace, **kwargs):
        """Create VM matching Harvester's exact structure."""

        # Optional node affinity — either explicit node_name or derived from sc_name
        node_name = kwargs.get('node_name') or ''
        sc_name = kwargs.get('sc_name') or ''
        if sc_name and not node_name:
            node_name = self._get_sc_node(sc_name)

        # Optional secondary VLAN NIC
        network_name = kwargs.get('network_name') or ''
        interfaces = [{"masquerade": {}, "model": "virtio", "name": "default"}]
        networks = [{"name": "default", "pod": {}}]
        if network_name:
            interfaces.append({"bridge": {}, "model": "virtio", "name": "vlan-nic"})
            networks.append({
                                "name": "vlan-nic",
                                "multus": {"networkName": f"default/{network_name}"}
                })

        # Look up the image's actual storage class from Harvester.
        try:
            img_obj = self.obj_api.get_namespaced_custom_object(
                group="harvesterhci.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualmachineimages",
                name=image_id
            )
            storage_class = img_obj.get("status", {}).get(
                "storageClassName", ""
            )
            if not storage_class:
                raise Exception(
                    f"Image {image_id} has no storageClassName in status"
                )
            logging(f"Resolved storage class for image {image_id}: "
                    f"{storage_class}")
        except ApiException as e:
            raise Exception(
                f"Failed to look up image {image_id} for storage class: {e}"
            )

        # Build volumeClaimTemplates annotation for Harvester
        volume_claim_templates = [
            {
                "metadata": {
                    "name": f"{vm_name}-disk-0",
                    "annotations": {
                        "harvesterhci.io/imageId": f"{namespace}/{image_id}"
                    }
                },
                "spec": {
                    "accessModes": ["ReadWriteMany"],
                    "resources": {"requests": {"storage": "10Gi"}},
                    "volumeMode": "Block",
                    "storageClassName": storage_class
                }
            }
        ]

        # Build complete VM spec matching Harvester structure
        body = {
            "apiVersion": f"{KUBEVIRT_API_GROUP}/{KUBEVIRT_API_VERSION}",
            "kind": "VirtualMachine",
            "metadata": {
                "name": vm_name,
                "namespace": namespace,
                "annotations": {
                    "harvesterhci.io/vmRunStrategy": "RerunOnFailure",
                    "harvesterhci.io/volumeClaimTemplates": (
                        json.dumps(volume_claim_templates)
                    ),
                    "harvesterhci.io/sshNames": "[]"
                },
                "labels": {
                    LABEL_TEST: LABEL_TEST_VALUE,
                    "harvesterhci.io/creator": "robot-framework",
                    "harvesterhci.io/os": "linux"
                }
            },
            "spec": {
                "runStrategy": "RerunOnFailure",
                "template": {
                    "metadata": {
                        "annotations": {
                            "harvesterhci.io/sshNames": "[]"
                        },
                        "labels": {
                            "harvesterhci.io/vmName": vm_name
                        }
                    },
                    "spec": {
                        "affinity": {},
                        "architecture": "amd64",
                        "domain": {
                            "cpu": {
                                "cores": int(cpu),
                                "sockets": 1,
                                "threads": 1
                            },
                            "devices": {
                                "disks": [
                                    {"bootOrder": 1, "disk": {"bus": "virtio"}, "name": "disk-0"},
                                    {"disk": {"bus": "virtio"}, "name": "cloudinit"}
                                ],
                                "inputs": [
                                    {
                                        "bus": "usb",
                                        "name": "tablet",
                                        "type": "tablet"
                                    }
                                ],
                                "interfaces": interfaces
                            },
                            "features": {
                                "acpi": {"enabled": True}
                            },
                            "machine": {"type": "q35"},
                            "memory": {
                                "guest": str(memory)
                            },
                            "resources": {
                                "limits": {
                                    "cpu": str(cpu),
                                    "memory": str(memory)
                                },
                                "requests": {
                                    "cpu": "125m",
                                    "memory": "2730Mi"
                                }
                            }
                        },
                        "evictionStrategy": "LiveMigrateIfPossible",
                        "hostname": vm_name,
                        "networks": networks,
                        "volumes": [
                            {"name": "disk-0",
                             "persistentVolumeClaim": {"claimName": f"{vm_name}-disk-0"}},
                            {"name": "cloudinit",
                             "cloudInitNoCloud": {"userData": DEFAULT_USER_DATA}}
                        ],
                        "terminationGracePeriodSeconds": 120
                    }
                }
            }
        }

        if node_name:
            body["spec"]["template"]["spec"]["affinity"] = {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [{
                            "matchExpressions": [{
                                "key": "kubernetes.io/hostname",
                                "operator": "In",
                                "values": [node_name]
                            }]
                        }]
                    }
                }
            }

        try:
            create_cr(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINE_PLURAL,
                body=body
            )
        except ApiException as e:
            logging(f"Failed to create VirtualMachine: {e}")
            raise

    def delete(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Delete VirtualMachine."""
        try:
            logging(f"Deleting VirtualMachine {namespace}/{vm_name}")

            try:
                delete_cr(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINE_PLURAL,
                    name=vm_name
                )
                logging(f"Deleted VirtualMachine {namespace}/{vm_name}")
            except ApiException as e:
                if e.status != 404:
                    raise

        except Exception as e:
            logging(f"Error deleting VM {vm_name}: {e}")
            raise

    def get(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Get VirtualMachine."""
        return get_cr(
            group=KUBEVIRT_API_GROUP,
            version=KUBEVIRT_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINE_PLURAL,
            name=vm_name
        )

    def list(self, namespace=DEFAULT_NAMESPACE, label_selector=None):
        """List VirtualMachines."""
        result = list_cr(
            group=KUBEVIRT_API_GROUP,
            version=KUBEVIRT_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINE_PLURAL,
            label_selector=label_selector
        )
        return result.get("items", [])

    def start(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Start a VM."""
        for i in range(self.retry_count):
            try:
                vm = self.get(vm_name, namespace)
                vm['spec']['runStrategy'] = 'Always'

                self.obj_api.replace_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINE_PLURAL,
                    name=vm_name,
                    body=vm
                )

                logging(f"VM {namespace}/{vm_name} started")
                return

            except ApiException as e:
                if e.status == 409:
                    logging(f"Conflict when starting VM, retrying ({i})...")
                    time.sleep(self.retry_interval)
                else:
                    raise

        raise AssertionError(
            f"Failed to start VM after {self.retry_count} attempts"
        )

    def stop(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Stop a VM."""
        for i in range(self.retry_count):
            try:
                vm = self.get(vm_name, namespace)
                vm['spec']['runStrategy'] = 'Halted'

                self.obj_api.replace_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINE_PLURAL,
                    name=vm_name,
                    body=vm
                )

                logging(f"VM {namespace}/{vm_name} stopped")
                return

            except ApiException as e:
                if e.status == 409:
                    logging(f"Conflict when stopping VM, retrying ({i})...")
                    time.sleep(self.retry_interval)
                else:
                    raise

        raise AssertionError(
            f"Failed to stop VM after {self.retry_count} attempts"
        )

    def restart(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Restart a VM."""
        logging(f"Restarting VM {namespace}/{vm_name}")
        try:
            # Create a restart subresource request
            self.obj_api.create_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINE_PLURAL,
                name=vm_name,
                body={}
            )
            logging(f"VM {namespace}/{vm_name} restart initiated")
        except ApiException as e:
            logging(f"Error restarting VM: {e}")
            raise

    def migrate(self, vm_name, target_node, namespace=DEFAULT_NAMESPACE):
        """Migrate VM to target node."""
        logging(
            f"Migrating VM {namespace}/{vm_name} to node {target_node}"
        )
        try:
            # Create VirtualMachineInstanceMigration object
            migration_body = {
                "apiVersion": f"{KUBEVIRT_API_GROUP}/{KUBEVIRT_API_VERSION}",
                "kind": "VirtualMachineInstanceMigration",
                "metadata": {
                    "name": f"{vm_name}-migration",
                    "namespace": namespace
                },
                "spec": {
                    "vmiName": vm_name
                }
            }

            self.obj_api.create_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachineinstancemigrations",
                body=migration_body
            )
            logging(
                f"VM {namespace}/{vm_name} migration to "
                f"{target_node} initiated"
            )
        except ApiException as e:
            logging(f"Error migrating VM: {e}")
            raise

    def wait_for_vm_created(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Wait for VM CR creation."""
        for i in range(self.retry_count):
            try:
                self.get(vm_name, namespace)
                logging(f"VirtualMachine {namespace}/{vm_name} created")
                return True
            except Exception:
                logging(f"Waiting for VM to be created ({i})...")
                time.sleep(self.retry_interval)

        raise AssertionError(
            f"VirtualMachine {namespace}/{vm_name} not created"
        )

    def wait_for_running(
            self, vm_name, timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait for VM to be running."""
        endtime = time.time() + timeout
        last_log_time = 0

        while time.time() < endtime:
            try:
                vmi = self.obj_api.get_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINEINSTANCE_PLURAL,
                    name=vm_name
                )

                phase = vmi.get('status', {}).get('phase', 'Unknown')

                if phase == 'Running':
                    logging(f"VM {namespace}/{vm_name} is running")
                    return True

                now = time.time()
                if now - last_log_time >= 30:
                    logging(
                        f"Waiting for VM {vm_name} to run (current phase: {phase})..."
                    )
                    last_log_time = now

            except ApiException as e:
                if e.status != 404:
                    logging(f"Error checking VM status: {e}")

            time.sleep(self.retry_interval)

        raise AssertionError(
            f"VM {namespace}/{vm_name} did not run within {timeout}s"
        )

    def wait_for_stopped(
            self, vm_name, timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait for VM to be stopped."""
        endtime = time.time() + timeout
        last_log_time = 0

        while time.time() < endtime:
            try:
                vmi = self.obj_api.get_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINEINSTANCE_PLURAL,
                    name=vm_name
                )

                phase = vmi.get('status', {}).get('phase', 'Unknown')
                now = time.time()
                if now - last_log_time >= 30:
                    logging(
                        f"Waiting for VM {vm_name} to stop (current phase: {phase})..."
                    )
                    last_log_time = now

            except ApiException as e:
                if e.status == 404:
                    logging(f"VM {namespace}/{vm_name} is stopped")
                    return True

            time.sleep(self.retry_interval)

        raise AssertionError(
            f"VM {namespace}/{vm_name} did not stop within {timeout}s"
        )

    def wait_for_deleted(
            self, vm_name, timeout=DEFAULT_TIMEOUT_SHORT, namespace=DEFAULT_NAMESPACE):
        """Wait for VM to be deleted."""
        wait_for_cr_deleted(
            group=KUBEVIRT_API_GROUP,
            version=KUBEVIRT_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINE_PLURAL,
            name=vm_name,
            timeout=timeout
        )

    def get_status(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Get VM status."""
        vm = self.get(vm_name, namespace)

        return {
            'runStrategy': vm.get('spec', {}).get('runStrategy', 'Unknown'),
            'conditions': vm.get('status', {}).get('conditions', [])
        }

    def wait_for_ip_addresses(
            self, vm_name, networks=None, timeout=DEFAULT_TIMEOUT_SHORT,
            namespace=DEFAULT_NAMESPACE):
        """Wait for VM to get IP addresses."""
        if networks is None:
            networks = ['default']
        elif isinstance(networks, str):
            # Handle case where Robot Framework passes string like "['default']"
            import ast
            try:
                networks = ast.literal_eval(networks)
            except (ValueError, SyntaxError):
                # If it's just a plain string, treat it as a single network
                networks = [networks]

        logging(
            f"Waiting for VM {namespace}/{vm_name} to get IP addresses "
            f"on networks: {networks}"
        )

        endtime = time.time() + timeout

        while time.time() < endtime:
            try:
                vmi = self.obj_api.get_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINEINSTANCE_PLURAL,
                    name=vm_name
                )

                interfaces = vmi.get('status', {}).get('interfaces', [])

                # Check each requested network for IP address
                got_all_ips = True
                for network in networks:
                    has_ip = any(
                        iface['name'] == network and iface.get('ipAddress')
                        for iface in interfaces
                    )
                    if not has_ip:
                        got_all_ips = False
                        logging(
                            f"Network '{network}' does not have IP yet"
                        )
                        break

                if got_all_ips:
                    # Log the IP addresses found
                    ips = {
                        iface['name']: iface.get('ipAddress')
                        for iface in interfaces
                        if iface['name'] in networks
                    }
                    logging(
                        f"VM {namespace}/{vm_name} got IP addresses: {ips}"
                    )
                    return True

                logging(
                    f"Waiting for VM to get IP addresses "
                    f"(networks: {networks}, {len(interfaces)} interfaces)..."
                )

            except ApiException as e:
                logging(f"Error checking VM IP: {e}")

            time.sleep(self.retry_interval)

        raise AssertionError(
            f"VM {namespace}/{vm_name} did not get IP addresses "
            f"within {timeout}s"
        )

    def cleanup(self):
        """Clean up test VMs."""
        logging('Cleaning up test VMs')

        try:
            vms = self.list(
                namespace=DEFAULT_NAMESPACE,
                label_selector=f"{LABEL_TEST}={LABEL_TEST_VALUE}"
            )

            for vm in vms:
                vm_name = vm['metadata']['name']
                namespace = vm['metadata']['namespace']

                try:
                    logging(f'Deleting test VM: {namespace}/{vm_name}')
                    self.delete(vm_name, namespace)
                except Exception as e:
                    logging(f'Error deleting VM {vm_name}: {e}', 'WARNING')
        except Exception as e:
            logging(f'Error during VM cleanup: {e}', 'WARNING')

    def create_for_lvm(self, vm_name, sc_name, image_id, network_name=None):
        """Create a VM with a Harvester image root disk and node affinity from the StorageClass"""
        node_name = self._get_sc_node(sc_name)
        self._create_vm_with_image(vm_name, image_id, node_name=node_name,
                                   network_name=network_name)
        logging(f"VM {vm_name} created")

    def create_vm_with_volume_using_sc(self, vm_name, sc_name, image_id, network_name=None):
        """Create a VM with a Harvester image root disk and
           an additional LVM StorageClass volume"""
        node_name = self._get_sc_node(sc_name)
        self._create_vm_with_image(vm_name, image_id, node_name=node_name,
                                   sc=sc_name, network_name=network_name)
        logging(f"VM {vm_name} with LVM volume created")

    def _get_sc_node(self, sc_name):
        """Get the node parameter from a StorageClass"""
        try:
            sc = self.storage_api.read_storage_class(name=sc_name)
            return sc.parameters.get("node", "")
        except ApiException:
            return ""

    def _get_image_storage_class(self, image_id, namespace=DEFAULT_NAMESPACE):
        """Look up the Harvester image's storageClassName from its status"""
        try:
            img_obj = self.obj_api.get_namespaced_custom_object(
                group="harvesterhci.io",
                version="v1beta1",
                namespace=namespace,
                plural="virtualmachineimages",
                name=image_id
            )
            storage_class = img_obj.get("status", {}).get("storageClassName", "")
            if not storage_class:
                raise Exception(f"Image {image_id} has no storageClassName in status")
            logging(f"Resolved storage class for image {image_id}: {storage_class}")
            return storage_class
        except ApiException as e:
            raise Exception(f"Failed to look up image {image_id}: {e}")

    def _create_vm_with_image(
            self, vm_name, image_id, namespace=DEFAULT_NAMESPACE,
            node_name=None, sc=None, network_name=None):
        """Create a VM using a Harvester image root disk,
        with optional node affinity and additional volume"""
        storage_class = self._get_image_storage_class(image_id, namespace)

        volume_claim_templates = [
            {
                "metadata": {
                    "name": f"{vm_name}-disk-0",
                    "annotations": {
                        "harvesterhci.io/imageId": f"{namespace}/{image_id}"
                    }
                },
                "spec": {
                    "accessModes": ["ReadWriteMany"],
                    "resources": {"requests": {"storage": "10Gi"}},
                    "volumeMode": "Block",
                    "storageClassName": storage_class
                }
            }
        ]
        disks = [
            {"name": "disk-0", "disk": {"bus": "virtio"}, "bootOrder": 1},
            {"name": "cloudinitdisk", "disk": {"bus": "virtio"}}
        ]
        volumes = [
            {"name": "disk-0", "persistentVolumeClaim": {"claimName": f"{vm_name}-disk-0"}},
            {
                "name": "cloudinitdisk",
                "cloudInitNoCloud": {
                    "userData": (
                        "#cloud-config\n"
                        "password: password\n"
                        "chpasswd:\n"
                        "  expire: false\n"
                        "ssh_pwauth: true\n"
                    )
                }
            }
        ]

        if sc:
            disks.append({"name": "lvm-disk", "disk": {"bus": "virtio"}})
            volumes.append({
                "name": "lvm-disk",
                "persistentVolumeClaim": {"claimName": f"{vm_name}-lvm-disk"}
            })
            volume_claim_templates.append({
                "metadata": {"name": f"{vm_name}-lvm-disk", "namespace": namespace},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "storageClassName": sc,
                    "resources": {"requests": {"storage": "5Gi"}},
                    "volumeMode": "Filesystem"
                }
            })

        body = {
            "apiVersion": f"{KUBEVIRT_API_GROUP}/{KUBEVIRT_API_VERSION}",
            "kind": "VirtualMachine",
            "metadata": {
                "name": vm_name,
                "namespace": namespace,
                "annotations": {
                    "harvesterhci.io/vmRunStrategy": RUN_STRATEGY_RERUN_ON_FAILURE,
                    "harvesterhci.io/volumeClaimTemplates": json.dumps(volume_claim_templates),
                    "harvesterhci.io/sshNames": "[]"
                },
                "labels": {
                    LABEL_TEST: LABEL_TEST_VALUE,
                    "harvesterhci.io/creator": "robot-framework"
                }
            },
            "spec": {
                "runStrategy": RUN_STRATEGY_RERUN_ON_FAILURE,
                "template": {
                    "metadata": {
                        "labels": {"harvesterhci.io/vmName": vm_name},
                        "annotations": {"harvesterhci.io/sshNames": "[]"}
                    },
                    "spec": {
                        "domain": {
                            "cpu": {"cores": 2, "sockets": 1, "threads": 1},
                            "devices": {
                                "disks": disks,
                                "interfaces": [{"masquerade": {},
                                                "model": "virtio", "name": "default"}]
                                + ([{"bridge": {}, "model": "virtio",
                                     "name": "vlan-nic"}] if network_name else [])
                            },
                            "machine": {"type": "q35"},
                            "memory": {"guest": "4Gi"},
                            "resources": {
                                "limits": {"cpu": "2", "memory": "4Gi"},
                                "requests": {"cpu": "125m", "memory": "2730Mi"}
                            }
                        },
                        "networks": [{"name": "default", "pod": {}}]
                        + ([{"name": "vlan-nic",
                             "multus": {"networkName": f"default/{network_name}"}}]
                           if network_name else []),
                        "volumes": volumes,
                        "hostname": vm_name
                    }
                }
            }
        }

        if node_name:
            body["spec"]["template"]["spec"]["affinity"] = {
                "nodeAffinity": {
                    "requiredDuringSchedulingIgnoredDuringExecution": {
                        "nodeSelectorTerms": [{
                            "matchExpressions": [{
                                "key": "kubernetes.io/hostname",
                                "operator": "In",
                                "values": [node_name]
                            }]
                        }]
                    }
                }
            }

        try:
            create_cr(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachines",
                body=body
            )
        except ApiException as e:
            raise Exception(f"Failed to create VM {vm_name}: {e}")

    def attach_volume(self, vm_name, vol_name, namespace=DEFAULT_NAMESPACE):
        """Attach an existing PVC to a VM (stop, patch volumes, start)"""
        logging(f"Attaching volume {vol_name} to VM {vm_name}")
        self.stop(vm_name)
        self._wait_for_lvm_vm_state(vm_name, VM_STATE_STOPPED, namespace)

        vm = get_cr(
            group=KUBEVIRT_API_GROUP,
            version=KUBEVIRT_API_VERSION,
            namespace=namespace,
            plural="virtualmachines",
            name=vm_name
        )
        spec = vm.get("spec", {}).get("template", {}).get("spec", {})
        disks = spec.get("domain", {}).get("devices", {}).get("disks", [])
        volumes_list = spec.get("volumes", [])

        disks.append({"name": vol_name, "disk": {"bus": "virtio"}})
        volumes_list.append({"name": vol_name, "persistentVolumeClaim": {"claimName": vol_name}})

        patch_body = {
            "spec": {
                "template": {
                    "spec": {
                        "domain": {"devices": {"disks": disks}},
                        "volumes": volumes_list
                    }
                }
            }
        }
        try:
            patch_cr(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachines",
                name=vm_name,
                body=patch_body
            )
        except ApiException as e:
            raise Exception(f"Failed to attach volume {vol_name} to VM {vm_name}: {e}")

        self.start(vm_name)
        self._wait_for_lvm_vm_state(vm_name, VM_STATE_RUNNING, namespace)

    def is_running(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return True if VM is in Running state"""
        try:
            vmi = self.obj_api.get_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachineinstances",
                name=vm_name
            )
            return vmi.get("status", {}).get("phase", "") == "Running"
        except ApiException:
            return False

    def is_stopped(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return True if VM is stopped (no VMI exists)"""
        try:
            self.obj_api.get_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachineinstances",
                name=vm_name
            )
            return False
        except ApiException as e:
            return e.status == 404

    def _wait_for_lvm_vm_state(self, vm_name, expected_state, namespace=DEFAULT_NAMESPACE,
                               timeout=DEFAULT_TIMEOUT):
        """Wait for VM to reach expected state"""
        endtime = time.time() + timeout
        while time.time() < endtime:
            if expected_state == VM_STATE_RUNNING and self.is_running(vm_name, namespace):
                return
            if expected_state == VM_STATE_STOPPED and self.is_stopped(vm_name, namespace):
                return
            time.sleep(self.retry_interval)
        raise AssertionError(f"VM {vm_name} did not reach state "
                             f"{expected_state} within {timeout}s")

    def _get_vmi_ip(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Get the IP address of a running VMI"""
        try:
            vmi = self.obj_api.get_namespaced_custom_object(
                group=KUBEVIRT_API_GROUP,
                version=KUBEVIRT_API_VERSION,
                namespace=namespace,
                plural="virtualmachineinstances",
                name=vm_name
            )
            for iface in vmi.get("status", {}).get("interfaces", []):
                ip = iface.get("ipAddress", "")
                if ip:
                    return ip
        except ApiException as e:
            raise Exception(f"Failed to get VMI IP for {vm_name}: {e}")
        raise Exception(f"No IP address found for VM {vm_name}")

    def _get_virt_launcher_pod(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Get the virt-launcher pod name for a VM"""
        try:
            pods = self.core_api.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"harvesterhci.io/vmName={vm_name}"
            )
            for pod in pods.items:
                if pod.metadata.name.startswith("virt-launcher") and pod.status.phase == "Running":
                    return pod.metadata.name
        except ApiException:
            pass
        return None

    def _wait_for_guest_agent(self, vm_name, namespace=DEFAULT_NAMESPACE,
                              timeout=DEFAULT_TIMEOUT_SHORT):
        """Wait until the QEMU guest agent reports as connected"""
        logging(f"Waiting for guest agent on VM {vm_name}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                vmi = self.obj_api.get_namespaced_custom_object(
                    group=KUBEVIRT_API_GROUP,
                    version=KUBEVIRT_API_VERSION,
                    namespace=namespace,
                    plural=VIRTUALMACHINEINSTANCE_PLURAL,
                    name=vm_name
                )
                for cond in vmi.get("status", {}).get("conditions", []):
                    if (cond.get("type") == "AgentConnected"
                            and cond.get("status") == "True"):
                        logging(f"Guest agent connected on VM {vm_name}")
                        return
            except ApiException:
                pass
            time.sleep(self.retry_interval)
        raise AssertionError(
            f"Guest agent not connected on VM {vm_name} within {timeout}s"
        )

    def _exec_in_vm(self, vm_name, namespace, commands):
        """Execute commands inside a VM via the qemu guest agent in the virt-launcher pod.

        Uses qemu:///session (the correct URI inside virt-launcher) and the
        domain name format '{namespace}_{vm_name}' that KubeVirt assigns.
        Polls guest-exec-status until the command exits and returns stdout.
        """
        pod_name = self._get_virt_launcher_pod(vm_name, namespace)
        if not pod_name:
            raise Exception(f"No virt-launcher pod found for VM {vm_name}")

        # KubeVirt names the libvirt domain <namespace>_<vm-name>
        domain = f"{namespace}_{vm_name}"
        full_command = " && ".join(commands)
        logging(f"Executing in VM {vm_name} via pod {pod_name}: {full_command}")

        # Wait for the guest agent to be ready before sending any commands.
        # The agent may not be connected immediately after a VM restart.
        self._wait_for_guest_agent(vm_name, namespace)

        # Step 1: start the command via guest-exec and obtain its PID
        exec_payload = json.dumps({
            "execute": "guest-exec",
            "arguments": {
                "path": "/bin/sh",
                "arg": ["-c", full_command],
                "capture-output": True
            }
        })
        start_result = stream(
            self.core_api.connect_get_namespaced_pod_exec,
            pod_name, namespace,
            command=["virsh", "qemu-agent-command", domain, exec_payload],
            stderr=True, stdin=False, stdout=True, tty=False
        )
        pid = _parse_virsh_output(start_result)["return"]["pid"]
        logging(f"Guest exec PID {pid} started in VM {vm_name}")

        # Step 2: poll guest-exec-status until the command exits (up to 120 s)
        status_payload = json.dumps({
            "execute": "guest-exec-status",
            "arguments": {"pid": pid}
        })
        status_cmd = ["virsh", "qemu-agent-command", domain, status_payload]
        for _ in range(120):
            time.sleep(1)
            status_result = stream(
                self.core_api.connect_get_namespaced_pod_exec,
                pod_name, namespace,
                command=status_cmd,
                stderr=True, stdin=False, stdout=True, tty=False
            )
            status = _parse_virsh_output(status_result)["return"]
            if status.get("exited"):
                import base64
                stdout = ""
                if status.get("out-data"):
                    stdout = base64.b64decode(status["out-data"]).decode()
                exit_code = status.get("exitcode", 0)
                if exit_code != 0:
                    stderr = ""
                    if status.get("err-data"):
                        stderr = base64.b64decode(status["err-data"]).decode()
                    raise Exception(
                        f"Command failed (exit {exit_code}) in VM {vm_name}.\n"
                        f"CMD : {full_command}\n"
                        f"STDOUT: {stdout}\nSTDERR: {stderr}"
                    )
                return stdout

        raise Exception(
            f"Command timed out after 120s in VM {vm_name}: {full_command}"
        )

    def _find_data_disk(self, vm_name, namespace=DEFAULT_NAMESPACE, expected_size=None):
        """Dynamically find the data disk device inside the VM.

        Runs lsblk to list raw disk devices, excludes vda (the root/image disk),
        and returns the first remaining virtio disk whose size matches expected_size
        (e.g. '5Gi'). When expected_size is None the size filter is skipped.
        """
        if expected_size:
            # Convert Kubernetes size notation to lsblk SIZE column format:
            # '5Gi' -> '5G', '512Mi' -> '512M', '1Ti' -> '1T'
            # Due to filesystem overhead Filesystem volume size is smaller than the
            # requested PVC capacity, so callers should omit expected_size.
            lsblk_size = expected_size.rstrip('i')
            cmd = (
                f"lsblk -d -n -o NAME,SIZE "
                f"| awk '/^vd/ && !/^vda/ && $2==\"{lsblk_size}\" {{print $1}}' "
                f"| head -1"
            )
        else:
            # Skip vda (root) and disks in the K/M range (e.g. cloud-init ISO ~1M).
            # Only return a disk whose size is reported in G/T range.
            cmd = (
                "lsblk -d -n -o NAME,SIZE "
                "| awk '/^vd/ && !/^vda/ && $2 ~ /[GT]$/ {print $1}' "
                "| head -1"
            )

        output = self._exec_in_vm(vm_name, namespace, [cmd])
        device_name = output.strip()
        if not device_name:
            size_hint = f" with size {expected_size}" if expected_size else ""
            raise AssertionError(
                f"No data disk found in VM {vm_name}: "
                f"no non-root virtio disk{size_hint} visible in lsblk"
            )
        device = f"/dev/{device_name}"
        logging(f"Discovered data disk {device} in VM {vm_name}")
        return device

    def check_block_device(self, vm_name, namespace=DEFAULT_NAMESPACE, expected_disk_size=None):
        """Assert a data disk (non-root virtio block device) is visible in the VM.

        When expected_disk_size is provided (e.g. '5Gi') the check also verifies
        the disk matches that size, avoiding confusion with other attached disks.

        Returns the discovered device path (e.g. '/dev/vdb') for use by callers.
        """
        logging(f"Checking data block device is visible in VM {vm_name}")
        device = self._find_data_disk(vm_name, namespace, expected_disk_size)
        logging(f"Data block device {device} confirmed in VM {vm_name}")
        return device

    def write_data_and_get_checksum_on_disk(
            self, vm_name, device, format_device=True, namespace=DEFAULT_NAMESPACE):
        """Write data to the given device inside the VM and return its md5sum.

        Formats the device to ext4 when format_device=True (Block volumes).
        Filesystem volumes are pre-formatted by the CSI driver; pass
        format_device=False to skip mkfs and mount directly.

        """
        logging(f"Writing data to {device} on VM {vm_name}")
        mount_point = f"/mnt/{vm_name}"
        commands = []
        if format_device:
            commands.append(f"mkfs.ext4 {device}")
        commands += [
            f"mkdir -p {mount_point}",
            f"mount {device} {mount_point}",
            f"dd if=/dev/urandom of={mount_point}/{DATA_FILE} bs=1M count=100",
            f"md5sum {mount_point}/{DATA_FILE} | awk '{{print $1}}'"
        ]
        output = self._exec_in_vm(vm_name, namespace, commands).strip()
        # mkfs prints multi-line noise; extract just the 32-char md5sum hash
        match = re.search(r'\b([0-9a-f]{32})\b', output)
        return match.group(1) if match else output

    def mount_data_disk(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Mount the data disk inside the VM after a restore.

        After a snapshot restore the data disk exists but is not mounted.
        This re-mounts it at BLOCK_DEVICE_MOUNT so subsequent md5sum checks
        can read the data.
        """
        logging(f"Mounting data disk in VM {vm_name}")
        mount_point = f"/mnt/{vm_name}"
        device = self._find_data_disk(vm_name, namespace)
        commands = [
            f"mkdir -p {mount_point}",
            f"mount {device} {mount_point} || true",
        ]
        self._exec_in_vm(vm_name, namespace, commands)
        logging(f"Data disk {device} mounted at {mount_point} in VM {vm_name}")

    def delete_data(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Delete test data from VM"""
        mount_point = f"/mnt/{vm_name}"
        commands = [f"rm -f {mount_point}/{DATA_FILE}"]
        self._exec_in_vm(vm_name, namespace, commands)

    def get_data_checksum(self, vm_name, namespace=DEFAULT_NAMESPACE):
        """Return md5sum checksum of test data in VM"""
        mount_point = f"/mnt/{vm_name}"
        commands = [f"md5sum {mount_point}/{DATA_FILE} | awk '{{print $1}}'"]
        output = self._exec_in_vm(vm_name, namespace, commands).strip()
        match = re.search(r'\b([0-9a-f]{32})\b', output)
        return match.group(1) if match else output

    def expand_volume_via_vm_edit(self, vm_name, vol_name, new_size, namespace=DEFAULT_NAMESPACE):
        """Expand volume by patching the VM volumeClaimTemplates annotation and PVC"""
        logging(f"Expanding volume {vol_name} on VM {vm_name} to {new_size}")
        vm = get_cr(group=KUBEVIRT_API_GROUP, version=KUBEVIRT_API_VERSION,
                    namespace=namespace, plural="virtualmachines", name=vm_name)
        annotations = vm.get("metadata", {}).get("annotations", {})
        vct_json = annotations.get("harvesterhci.io/volumeClaimTemplates", "[]")
        try:
            vcts = json.loads(vct_json)
        except (json.JSONDecodeError, TypeError):
            vcts = []
        for vct in vcts:
            if vct.get("metadata", {}).get("name") == vol_name:
                vct["spec"]["resources"]["requests"]["storage"] = new_size
                break
        patch_body = {
            "metadata": {
                "annotations": {
                    "harvesterhci.io/volumeClaimTemplates": json.dumps(vcts)
                }
            }
        }
        try:
            patch_cr(group=KUBEVIRT_API_GROUP, version=KUBEVIRT_API_VERSION,
                     namespace=namespace, plural="virtualmachines",
                     name=vm_name, body=patch_body)
        except ApiException as e:
            raise Exception(f"Failed to expand volume via VM edit: {e}")
        # Also patch the PVC directly
        pvc_patch = {"spec": {"resources": {"requests": {"storage": new_size}}}}
        try:
            self.core_api.patch_namespaced_persistent_volume_claim(
                name=vol_name, namespace=namespace, body=pvc_patch)
            logging(f"PVC {vol_name} expanded to {new_size}")
        except ApiException as e:
            raise Exception(f"Failed to expand PVC {vol_name}: {e}")

    def verify_volume_size(self, vm_name, expected_size, namespace=DEFAULT_NAMESPACE):
        """Verify volume size inside VM matches expected (uses lsblk)"""
        from constant import GIBIBYTE
        logging(f"Verifying volume size in VM {vm_name}, expected={expected_size}")
        commands = ["lsblk -b -o NAME,SIZE --json"]
        try:
            result = self._exec_in_vm(vm_name, namespace, commands)
            size_value = int(expected_size.replace("Gi", ""))
            expected_bytes = size_value * GIBIBYTE
            import json as _json
            try:
                block_info = _json.loads(result)
                for device in block_info.get("blockdevices", []):
                    size = int(device.get("size", 0))
                    if abs(size - expected_bytes) < (expected_bytes * 0.05):
                        return True
                    for child in device.get("children", []):
                        size = int(child.get("size", 0))
                        if abs(size - expected_bytes) < (expected_bytes * 0.05):
                            return True
            except (_json.JSONDecodeError, TypeError):
                logging("Failed to parse lsblk output")
            return False
        except Exception as e:
            logging(f"Error verifying volume size in VM: {e}")
            return False
