""" Forklift Keyword Wrapper

Layer 3: Keyword wrapper (NO direct API calls)

Covers the virt-v2v image the SUSE VM Migration Toolkit (Forklift addon)
converts guests with (harvester/forklift-packaging#24; harvester/harvester
#11657, #11775, #11851) and cold migrations from a vSphere provider.
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))  # noqa E402
from forklift import Forklift  # noqa E402
from utility.utility import logging  # noqa E402

# Marker of the perl-Bootloader patch (libguestfs/libguestfs-common#56)
PERL_BOOTLOADER_WARNING = "Bootloader::Tools, ignoring"


def _version_tuple(text):
    return tuple(int(x) for x in text.split("."))


class forklift_keywords:
    """Forklift keyword wrapper - creates the Forklift component and delegates"""

    def __init__(self):
        self._forklift = None

    @property
    def forklift(self):
        """Lazy initialize to allow API client setup first"""
        if self._forklift is None:
            self._forklift = Forklift()
        return self._forklift

    # ---- virt-v2v image probe ----

    def get_virt_v2v_image(self):
        image = self.forklift.get_virt_v2v_image()
        assert image, "forklift-controller has no VIRT_V2V_IMAGE configured"
        logging(f"Forklift converts guests with {image}")
        return image

    def start_virt_v2v_probe(self, pod_name, image=""):
        """Probe image, or the image Forklift is configured with when empty."""
        image = image or self.get_virt_v2v_image()
        self.forklift.start_image_probe(image, pod_name)
        return image

    def stop_virt_v2v_probe(self, pod_name):
        self.forklift.delete_probe(pod_name)

    def probe_command_should_succeed(self, pod_name, command, timeout=600):
        result = self.forklift.exec_in_probe(pod_name, command, int(timeout))
        assert result["rc"] == 0, (
            f"'{command}' failed in the virt-v2v image (rc={result['rc']}):\n"
            f"{result['output'][-3000:]}")
        return result["output"]

    def run_probe_command(self, pod_name, command, timeout=600):
        return self.forklift.exec_in_probe(pod_name, command, int(timeout))["output"]

    def virt_v2v_version_should_be_at_least(self, pod_name, minimum):
        output = self.probe_command_should_succeed(pod_name, "virt-v2v --version")
        match = re.search(r"virt-v2v (\d+\.\d+(?:\.\d+)?)", output)
        assert match, f"Cannot parse the virt-v2v version from: {output}"
        version = match.group(1)
        assert _version_tuple(version) >= _version_tuple(minimum), (
            f"virt-v2v {version} is older than {minimum}")
        return version

    def virt_v2v_should_support_features(self, pod_name, *features):
        output = self.probe_command_should_succeed(pod_name, "virt-v2v --machine-readable")
        lines = {line.strip() for line in output.splitlines()}
        missing = [f for f in features if f not in lines]
        assert not missing, f"virt-v2v lacks features {missing}: {sorted(lines)}"

    def libvirt_should_have_vpx_driver(self, pod_name):
        """Connecting to a vpx:// URI must reach the network (and fail
        there), not stop at a libvirt built without the vpx driver."""
        output = self.run_probe_command(
            pod_name,
            "virsh -c 'vpx://127.0.0.1/dc/host?no_verify=1' uri </dev/null",
            timeout=60)
        no_driver = ("without the 'vpx' driver" in output
                     or "no connection driver available" in output)
        assert not no_driver, f"libvirt in the virt-v2v image has no vpx driver: {output}"

    def files_should_exist_in_image(self, pod_name, *paths):
        quoted = " ".join(f"'{p}'" for p in paths)
        script = f'for f in {quoted}; do test -s "$f" || echo "missing $f"; done'
        output = self.run_probe_command(pod_name, script)
        missing = [line for line in output.splitlines() if line.startswith("missing ")]
        assert not missing, f"virt-v2v image is missing: {missing}"

    def directory_should_not_be_empty_in_image(self, pod_name, path):
        output = self.run_probe_command(pod_name, f"ls -A '{path}' 2>&1 | head -5")
        assert output.strip() and "No such file" not in output, (
            f"{path} is empty or missing in the virt-v2v image: {output}")

    def virt_v2v_should_tolerate_perl_bootloader_failures(self, pod_name):
        output = self.run_probe_command(
            pod_name, f"grep -c '{PERL_BOOTLOADER_WARNING}' \"$(command -v virt-v2v)\"")
        count = output.strip().splitlines()[-1] if output.strip() else "0"
        assert count.isdigit() and int(count) > 0, (
            "virt-v2v does not carry the perl-Bootloader fallback "
            "(libguestfs/libguestfs-common#56): SLES 15 conversions abort "
            "with 'no $default->{image}'")

    def libguestfs_appliance_should_boot_with_inspection_tools(self, pod_name, timeout=900):
        output = self.probe_command_should_succeed(
            pod_name, "libguestfs-test-tool", timeout=timeout)
        assert "TEST FINISHED OK" in output, (
            f"libguestfs appliance did not boot:\n{output[-3000:]}")
        output = self.probe_command_should_succeed(
            pod_name, "guestfish -a /dev/null run : debug sh 'command -v file'",
            timeout=timeout)
        assert "/file" in output, (
            "The libguestfs appliance has no 'file' binary; OS inspection "
            f"fails with 'execvp: file': {output[-1000:]}")

    # ---- migration ----

    def provider_should_be_ready(self, name):
        provider = self.forklift.get_provider(name)
        assert provider is not None, f"Forklift Provider {name} not found"
        conditions = {c["type"]: c for c in provider.get("status", {}).get("conditions", [])}
        failed = conditions.get("ConnectionTestFailed", {})
        usable = (conditions.get("Ready", {}).get("status") == "True"
                  and failed.get("status") != "True")
        assert usable, f"Forklift Provider {name} is not usable: {list(conditions.values())}"

    def create_migration_plan(self, name, source_provider, storage_map, network_map,
                              vm_name, target_namespace):
        self.forklift.create_plan(name, source_provider, storage_map, network_map,
                                  vm_name, target_namespace)

    def wait_for_plan_ready(self, name, timeout=600):
        deadline = time.time() + int(timeout)
        conditions = []
        while time.time() < deadline:
            conditions = self.forklift.get_plan(name).get("status", {}).get("conditions", [])
            if any(c["type"] == "Ready" and c["status"] == "True" for c in conditions):
                return
            critical = [c for c in conditions if c.get("category") == "Critical"]
            assert not critical, f"Plan {name} is invalid: {critical}"
            time.sleep(5)
        raise AssertionError(f"Plan {name} did not become Ready: {conditions}")

    def start_migration(self, name, plan_name):
        self.forklift.start_migration(name, plan_name)

    def wait_for_migration_succeeded(self, name, timeout=7200):
        deadline = time.time() + int(timeout)
        status = {}
        while time.time() < deadline:
            status = self.forklift.get_migration(name).get("status", {})
            types = {c["type"]: c["status"] for c in status.get("conditions", [])}
            if types.get("Succeeded") == "True":
                return
            if types.get("Failed") == "True" or types.get("Canceled") == "True":
                vms = status.get("vms", [])
                raise AssertionError(f"Migration {name} failed: {vms or status}")
            time.sleep(15)
        raise AssertionError(f"Migration {name} did not finish in {timeout}s: {status}")

    def get_migrated_vm_name(self, plan_name, source_vm_name):
        """Name of the VM Forklift created: the plan status carries newName
        when the source name is not a valid Kubernetes name."""
        vms = self.forklift.get_plan(plan_name).get("status", {}) \
            .get("migration", {}).get("vms", [])
        for vm in vms:
            if vm.get("name") == source_vm_name:
                return vm.get("newName") or vm["name"]
        return re.sub(r"[^a-z0-9-]+", "-", source_vm_name.lower()).strip("-")

    def delete_migration_plan(self, plan_name, migration_name, target_namespace):
        """Remove the Migration and Plan, and the volumes migrated for it."""
        self.forklift.delete_migration(migration_name)
        self.forklift.delete_plan_volumes(plan_name, target_namespace)
        self.forklift.delete_plan(plan_name)
