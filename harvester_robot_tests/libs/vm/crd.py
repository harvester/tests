"""
VM CRD Implementation
"""
import json
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import get_cr, create_cr, delete_cr, list_cr, wait_for_cr_deleted
from constant import (
    KUBEVIRT_API_GROUP, KUBEVIRT_API_VERSION,
    VIRTUALMACHINE_PLURAL, VIRTUALMACHINEINSTANCE_PLURAL,
    DEFAULT_NAMESPACE, LABEL_TEST, LABEL_TEST_VALUE,
    DEFAULT_TIMEOUT_SHORT
)
from utility.utility import logging, get_retry_count_and_interval
from vm.base import Base


class CRD(Base):
    """
    VM CRD implementation - uses Kubernetes Custom Resources
    """

    def __init__(self):
        """Initialize CRD client."""
        self.obj_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
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
                    "storageClassName": f"longhorn-{image_id}"
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
                                "inputs": [
                                    {
                                        "bus": "usb",
                                        "name": "tablet",
                                        "type": "tablet"
                                    }
                                ],
                                "interfaces": [
                                    {
                                        "masquerade": {},
                                        "model": "virtio",
                                        "name": "default"
                                    }
                                ]
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
                        "networks": [
                            {"name": "default", "pod": {}}
                        ],
                        "terminationGracePeriodSeconds": 120
                    }
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

                logging(
                    f"Waiting for VM to run (current phase: {phase})..."
                )

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
                logging(
                    f"Waiting for VM to stop (current phase: {phase})..."
                )

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
