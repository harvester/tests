import pytest


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
