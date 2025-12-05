from time import sleep
from datetime import datetime, timedelta
import subprocess
import tempfile
import os
import json

import pytest
import requests

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks",
]


@pytest.mark.p1
@pytest.mark.experimental
@pytest.mark.addons
class TestVMDHCPControllerAddon:
    """
    Test VM DHCP Controller Addon functionality

    Note: This is an experimental addon which is not installed in Harvester
    by default.
    Reference: https://docs.harvesterhci.io/v1.6/advanced/addons/managed-dhcp
    Installation: Download from
    https://raw.githubusercontent.com/harvester/experimental-addons/
    """

    addon_id = 'harvester-system/harvester-vm-dhcp-controller'
    addon_url = (
        'https://raw.githubusercontent.com/harvester/experimental-addons/'
        'main/harvester-vm-dhcp-controller/'
        'harvester-vm-dhcp-controller.yaml'
    )

    @pytest.mark.dependency(name="vmdhcp_download")
    def test_download_and_install_vm_dhcp_addon(
            self, api_client, wait_timeout):
        """
        Test downloading and installing VM DHCP Controller experimental addon

        Steps:
            1. Check if addon already exists
            2. If not exists, download addon manifest from experimental repo
            3. Apply the addon manifest using kubectl
            4. Wait for addon to be available

        Expected Result:
            - Addon should be created in Harvester
            - Addon should be in disabled state initially

        Note: Requires kubectl configured to access the Harvester cluster.
              Experimental addons cannot be created via Harvester API
        """
        # Check if addon already exists
        code, data = api_client.addons.get(self.addon_id)
        if code == 200:
            return

        # Download addon manifest
        try:
            response = requests.get(self.addon_url, timeout=30)
            response.raise_for_status()
            addon_manifest_text = response.text
        except Exception as e:
            pytest.skip(f"Failed to download experimental addon: {e}")

        # Apply addon manifest using kubectl
        manifest_file = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.yaml', delete=False) as f:
                f.write(addon_manifest_text)
                manifest_file = f.name

            result = subprocess.run(
                ['kubectl', 'apply', '-f', manifest_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=60
            )

            if result.returncode != 0:
                pytest.skip(
                    f"Failed to apply addon manifest: {result.stderr}\n"
                    "Ensure kubectl is configured to access the Harvester cluster"
                )

        except FileNotFoundError:
            pytest.skip(
                "kubectl command not found. Please install kubectl to run this test")
        except Exception as e:
            pytest.skip(f"Failed to install experimental addon: {e}")
        finally:
            # Clean up temp file
            if manifest_file:
                try:
                    os.unlink(manifest_file)
                except Exception:
                    pass

        # Wait for addon to be available
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.addons.get(self.addon_id)
            if code == 200:
                assert not data.get('spec', {}).get('enabled', True), (
                    "Newly installed addon should be disabled by default"
                )
                return
            sleep(5)
        else:
            raise AssertionError(
                f"Addon '{self.addon_id}' did not become available within "
                f"{wait_timeout} seconds after installation"
            )

    @pytest.mark.dependency(name="vmdhcp_enable", depends=["vmdhcp_download"])
    def test_enable_vm_dhcp_addon(self, api_client, wait_timeout):
        """
        Test enabling VM DHCP Controller addon

        Steps:
            1. Enable the harvester-vm-dhcp-controller addon
            2. Wait for addon to be deployed successfully
            3. Verify addon status changes to deployed

        Expected Result:
            - Addon should be enabled
            - Status should be 'deployed' or 'AddonDeploySuccessful'
            - DHCP controller should be ready to manage VM IP allocations
        """
        code, data = api_client.addons.enable(self.addon_id)

        assert 200 == code, (code, data)
        assert data.get('spec', {}).get('enabled', False), (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.addons.get(self.addon_id)
            status = data.get('status', {}).get('status', "")
            if status in ("deployed", "AddonDeploySuccessful"):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to enable addon {self.addon_id} with "
                f"{wait_timeout} timed out\n"
                f"API Status({code}): {data}"
            )

    @pytest.mark.dependency(name="vmdhcp_verify_enabled",
                            depends=["vmdhcp_enable"])
    def test_verify_vm_dhcp_controller(
            self, request, api_client, image_opensuse, unique_name,
            vlan_id, wait_timeout):
        """
        Test verifying VM DHCP Controller functionality.
        Test requires IP pool configuration in config.yml

        Steps:
            1. Create a VM network (VLAN)
            2. Configure an IP pool with specific subnet and IP range
            3. Create a VM with the network that has the IP pool
            4. Verify the VM gets an IP from the defined pool range
            5. Clean up resources (VM, IP pool, network)

        Expected Result:
            - VM should receive an IP address from the IP pool
            - IP should be within the configured pool range
        """
        # Get IP pool configuration from config
        ippool_subnet = request.config.getoption('--ip-pool-subnet')
        ippool_start = request.config.getoption('--ip-pool-start')
        ippool_end = request.config.getoption('--ip-pool-end')

        # Validate IP pool configuration
        if not ippool_subnet or not ippool_start or not ippool_end:
            pytest.skip(
                "IP pool configuration is required for DHCP test. "
                "Please set ip-pool-subnet, ip-pool-start, and "
                "ip-pool-end in config.yml"
            )

        # Step 1: Create a VM network (VLAN)
        network_name = f"dhcp-test-net-{unique_name}"
        code, network_data = api_client.networks.create(
            network_name, vlan_id, cluster_network='mgmt'
        )
        assert 201 == code, (
            f"Failed to create network: {code}, {network_data}"
        )

        network_id = f"default/{network_name}"

        # Step 2: Configure a DHCP IP pool with specific subnet and range
        ippool_name = f"dhcp-test-pool-{unique_name}"

        server_ip_parts = ippool_start.split('.')
        server_ip_parts[3] = str(max(1, int(server_ip_parts[3]) - 1))

        # Gateway/router is typically the first IP in the subnet
        gateway_parts = ippool_subnet.split('/')[0].split('.')
        gateway_parts[3] = '1'
        gateway_ip = '.'.join(gateway_parts)

        try:
            # Create DHCP IPPool using kubectl
            # (API doesn't support network.harvesterhci.io IPPools)
            ippool_yaml = f"""apiVersion: loadbalancer.harvesterhci.io/v1beta1
kind: IPPool
metadata:
  name: {ippool_name}
  namespace: default
spec:
  ranges:
    - gateway: {gateway_ip}
      rangeEnd: {ippool_end}
      rangeStart: {ippool_start}
      subnet: {ippool_subnet}
  selector:
    network: {network_id}
"""

            manifest_file = None
            try:
                with tempfile.NamedTemporaryFile(
                        mode='w', suffix='.yaml', delete=False) as f:
                    f.write(ippool_yaml)
                    manifest_file = f.name

                # Apply the DHCP IPPool manifest
                result = subprocess.run(
                    ['kubectl', 'apply', '-f', manifest_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=30
                )

                if result.returncode != 0:
                    raise AssertionError(
                        f"Failed to create DHCP IPPool: {result.stderr}"
                    )

            finally:
                if manifest_file:
                    try:
                        os.unlink(manifest_file)
                    except Exception:
                        pass

            # Wait for DHCP IP pool to become Ready
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                result = subprocess.run(
                    ['kubectl', 'get', 'ippools.loadbalancer',
                     ippool_name, '-o', 'json'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=30
                )

                if result.returncode == 0:
                    ippool_status = json.loads(result.stdout)
                    conditions = ippool_status.get(
                        'status', {}
                    ).get('conditions', [])

                    # Check for Registered conditions
                    registered = any(
                        c.get('type') == 'Ready' and
                        c.get('status') == 'True'
                        for c in conditions
                    )
                    if registered:
                        ippool_status.get(
                            'status', {}
                        ).get('ipv4', {}).get('available', 0)
                        break

                sleep(5)
            else:
                print(
                    f"DHCP IP pool failed to become fully Ready "
                    f"within {wait_timeout} seconds"
                )

            # Step 3: Create a VM with the network that has the IP pool
            vm_name = f"dhcp-test-vm-{unique_name}"

            # Check if image exists, create if not
            code, data = api_client.images.get(image_opensuse.name)
            if code == 404:
                code, data = api_client.images.create_by_url(
                    image_opensuse.name, image_opensuse.url
                )
                assert 201 == code, f"Failed to create image: {code}, {data}"

                # Wait for image download to complete
                endtime = datetime.now() + timedelta(seconds=wait_timeout)
                while endtime > datetime.now():
                    code, data = api_client.images.get(image_opensuse.name)
                    if (200 == code and
                            data.get('status', {}).get('progress') == 100):
                        break
                    sleep(5)
                else:
                    raise AssertionError(
                        f"Image download timed out after {wait_timeout} "
                        "seconds"
                    )

            spec = api_client.vms.Spec(1, 2)  # 1 CPU, 2GB RAM
            spec.add_image(image_opensuse.name,
                           f"default/{image_opensuse.name}")

            # Add the DHCP-enabled network
            spec.add_network("dhcp-net", network_id)

            code, vm_data = api_client.vms.create(vm_name, spec)
            assert 201 == code, f"Failed to create VM: {code}, {vm_data}"

            vm_namespace = vm_data.get('metadata', {}).get(
                'namespace', 'default'
            )

            # Wait for VM to be in running state
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                code, vm_status = api_client.vms.get_status(
                    vm_name, namespace=vm_namespace
                )
                if 200 == code:
                    vm_state = vm_status.get('status', {}).get('phase', '')
                    if vm_state == 'Running':
                        break
                sleep(5)
            else:
                raise AssertionError(
                    f"VM {vm_name} did not reach Running state within "
                    f"{wait_timeout} seconds"
                )

            # Step 4: Verify the VM gets an IP from the defined pool range
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            vm_ip = None

            while endtime > datetime.now():
                code, data = api_client.vms.get_status(
                    vm_name, namespace=vm_namespace
                )
                assert 200 == code, (
                    f"Failed to get VM status: {code}, {data}"
                )

                interfaces = data.get('status', {}).get('interfaces', [])

                # Check if VM has received ANY IP (on default interface)
                default_has_ip = False
                dhcp_net_has_ip = False

                for iface in interfaces:
                    if (iface.get('name') == 'default' and
                            'ipAddress' in iface and iface['ipAddress']):
                        default_has_ip = True

                    if iface.get('name') == 'dhcp-net':
                        if 'ipAddress' in iface and iface['ipAddress']:
                            vm_ip = iface['ipAddress']
                            dhcp_net_has_ip = True
                            break

                # If VM has IP on default but not on dhcp-net,
                # fail immediately
                if default_has_ip and not dhcp_net_has_ip:
                    raise AssertionError(
                        f"DHCP IP assignment failed but VM has IP on default "
                        f"VM Status interfaces: {interfaces}"
                    )

                if dhcp_net_has_ip:
                    break

                sleep(5)
            else:
                raise AssertionError(
                    "DHCP IP assignment failed: VM did not receive IP "
                    f"VM Status: {data}"
                )

            # Validate IP address format
            assert vm_ip, f"VM {vm_name} IP address is empty"
            ip_parts = vm_ip.split('.')
            assert len(ip_parts) == 4, f"Invalid IP address format: {vm_ip}"

            # Verify all octets are numeric
            for part in ip_parts:
                assert part.isdigit(), (
                    f"Invalid IP address format: {vm_ip}"
                )
                assert 0 <= int(part) <= 255, (
                    f"Invalid IP octet value in: {vm_ip}"
                )

            # Validate IP is within the configured pool range
            def ip_to_int(ip_str):
                """Convert IP address string to integer for comparison"""
                parts = [int(p) for p in ip_str.split('.')]
                return ((parts[0] << 24) + (parts[1] << 16) +
                        (parts[2] << 8) + parts[3])

            vm_ip_int = ip_to_int(vm_ip)
            start_ip_int = ip_to_int(ippool_start)
            end_ip_int = ip_to_int(ippool_end)

            assert start_ip_int <= vm_ip_int <= end_ip_int, (
                f"VM IP {vm_ip} is NOT within the configured IP pool "
                f"range {ippool_start} - {ippool_end}")

        finally:
            # Step 5: Clean up resources
            # Delete VM
            try:
                code, data = api_client.vms.delete(
                    vm_name, namespace=vm_namespace
                )
            except Exception as e:
                print(f"Exception during VM deletion: {e}")

            # Delete DHCP IP pool using kubectl
            try:
                result = subprocess.run(
                    ['kubectl', 'delete', 'ippools.loadbalancer', ippool_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    timeout=30
                )
            except Exception as e:
                print(
                    f"Exception during DHCP IP pool deletion: {e}"
                )

            # Delete network
            try:
                code, data = api_client.networks.delete(network_name)
            except Exception as e:
                print(f"Exception during network deletion: {e}")

    @pytest.mark.dependency(depends=["vmdhcp_verify_enabled"])
    def test_disable_vm_dhcp_addon(self, api_client, wait_timeout):
        """
        Test disabling VM DHCP Controller addon

        Steps:
            1. Disable the harvester-vm-dhcp-controller addon
            2. Wait for addon to be disabled
            3. Verify addon status changes to disabled

        Expected Result:
            - Addon should be disabled
            - Status should contain 'Disabled'
        """
        code, data = api_client.addons.disable(self.addon_id)

        assert 200 == code, (code, data)
        assert not data.get('spec', {}).get('enabled', True), (code, data)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.addons.get(self.addon_id)
            if "Disabled" in data.get('status', {}).get('status', ""):
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to disable addon {self.addon_id} with "
                f"API Status({code}): {data}"
            )
