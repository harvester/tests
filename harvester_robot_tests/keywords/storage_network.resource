*** Settings ***
Documentation    Storage Network Keywords - Reusable keywords for storage network operations
Library          ../libs/keywords/storage_network_keywords.py
Resource         variables.resource

*** Keywords ***
# Storage Network Operations
Enable
    [Arguments]    ${vlan_id}    ${cluster_network}    ${ip_range}    ${share_rwx}=${FALSE}
    [Documentation]    Enable the storage-network Harvester setting.
    ...               Args:
    ...                   vlan_id: VLAN ID for the storage network
    ...                   cluster_network: Cluster network name
    ...                   ip_range: CIDR IP range for storage network
    ...                   share_rwx: If True, share storage network for RWX volumes
    Log    Enabling storage network: vlan=${vlan_id}, cluster=${cluster_network}, share_rwx=${share_rwx}
    storage_network_keywords.enable_storage_network    ${vlan_id}    ${cluster_network}    ${ip_range}    ${share_rwx}

Disable
    [Documentation]    Disable the storage-network Harvester setting.
    Log    Disabling storage network
    storage_network_keywords.disable_storage_network

Get Status
    [Documentation]    Get the current storage-network setting status.
    Log    Getting storage network status
    ${status}=    storage_network_keywords.get_storage_network_status
    RETURN    ${status}

Wait For Ready
    [Arguments]    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for storage-network to be applied and completed.
    Log    Waiting for storage network to be ready
    ${data}=    storage_network_keywords.wait_for_storage_network_ready    ${timeout}
    RETURN    ${data}

Get Vlan Network CIDR
    [Arguments]    ${vlan_id}    ${cluster_network}
    [Documentation]    Get the CIDR for a VLAN network by creating a temp network.
    Log    Getting VLAN network CIDR for vlan=${vlan_id}
    ${cidr}=    storage_network_keywords.get_vlan_network_cidr    ${vlan_id}    ${cluster_network}
    RETURN    ${cidr}

Enable Longhorn RWX
    [Documentation]    Set the Longhorn endpoint-network-for-rwx-volume setting
    ...               to the same NAD used by Longhorn's storage-network setting.
    ...               The NAD reference is read dynamically (not hardcoded).
    Log    Setting Longhorn RWX endpoint network
    storage_network_keywords.enable_longhorn_rwx_storage_network

Disable Longhorn RWX
    [Documentation]    Clear the Longhorn endpoint-network-for-rwx-volume setting.
    Log    Clearing Longhorn RWX endpoint network
    storage_network_keywords.disable_longhorn_rwx_storage_network
