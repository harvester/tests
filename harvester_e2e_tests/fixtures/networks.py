import json

import pytest
from .base import wait_until


@pytest.fixture(scope="session")
def vlan_id(request):
    vlan_id = request.config.getoption('--vlan-id')
    assert 0 < vlan_id < 4095, f"VLAN ID should be in range 1-4094, not {vlan_id}"
    return vlan_id


@pytest.fixture(scope="session")
def vlan_nic(request):
    vlan_nic = request.config.getoption('--vlan-nic')
    assert vlan_nic, f"VLAN NIC {vlan_nic} not configured correctly."
    return vlan_nic


@pytest.fixture(scope="session")
def network_checker(api_client, wait_timeout, sleep_timeout):
    class NetworkChecker:
        def __init__(self):
            self.networks = api_client.networks
            self.clusternetworks = api_client.clusternetworks

        @wait_until(wait_timeout, sleep_timeout)
        def wait_routed(self, vnet_name):
            code, data = self.networks.get(vnet_name)
            annotations = data['metadata'].get('annotations', {})
            route = json.loads(annotations.get('network.harvesterhci.io/route', '{}'))
            if code == 200 and route.get('connectivity') == 'true':
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_cnet_config_created(self, cnet_config_name):
            code, data = api_client.clusternetworks.get_config(cnet_config_name)
            if code == 200:
                return True, (code, data)
            return False, (code, data)

        @wait_until(wait_timeout, sleep_timeout)
        def wait_vnet_deleted(self, vnet_name):
            code, data = api_client.networks.get(vnet_name)
            if code == 404:
                return True, (code, data)
            return False, (code, data)

    return NetworkChecker()
