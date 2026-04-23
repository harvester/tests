*** Settings ***
Documentation    Network Keywords - Reusable keywords for network operations
Library          ../libs/keywords/network_keywords.py
Resource         variables.resource

*** Keywords ***
# Cluster Network Operations
Network - Create Cluster Network
    [Arguments]    ${name}
    [Documentation]    Create cluster network.
    ...               Args:
    ...                   name: Cluster network name
    ...               Returns:
    ...                   dict: Cluster network data
    Log    Creating cluster network: ${name}
    ${cn}=    create_cluster_network    ${name}
    RETURN    ${cn}

Network - Delete Cluster Network
    [Arguments]    ${name}
    [Documentation]    Delete cluster network.
    ...               Args:
    ...                   name: Cluster network name
    Log    Deleting cluster network: ${name}
    delete_cluster_network    ${name}

Network - Create VLAN Config
    [Arguments]    ${name}    ${cluster_network}    ${nic}
    [Documentation]    Create VLAN config to bind NIC to cluster network.
    ...               Args:
    ...                   name: VLAN config name
    ...                   cluster_network: Cluster network name
    ...                   nic: NIC name (e.g., eno50)
    ...               Returns:
    ...                   dict: VLAN config data
    Log    Creating VLAN config: ${name}
    ${vc}=    create_vlan_config    ${name}    ${cluster_network}    ${nic}
    RETURN    ${vc}

Network - Delete VLAN Config
    [Arguments]    ${name}
    [Documentation]    Delete VLAN config.
    ...               Args:
    ...                   name: VLAN config name
    Log    Deleting VLAN config: ${name}
    delete_vlan_config    ${name}

Network - Wait For Cluster Network Ready
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for cluster network to become ready.
    ...               Args:
    ...                   name: Cluster network name
    ...                   timeout: Wait timeout in seconds
    ...               Returns:
    ...                   dict: Cluster network data when ready
    Log    Waiting for cluster network ${name} to be ready
    ${cn}=    wait_for_cluster_network_ready    ${name}    ${timeout}
    RETURN    ${cn}

# VLAN Network Operations
Network - Create VLAN Network
    [Arguments]    ${name}    ${vlan_id}    ${cluster_network}
    [Documentation]    Create VLAN network.
    ...               Args:
    ...                   name: Network name
    ...                   vlan_id: VLAN ID
    ...                   cluster_network: Cluster network name
    ...               Returns:
    ...                   dict: Network data
    Log    Creating VLAN network: ${name}
    ${network}=    create_vlan_network    ${name}    ${vlan_id}    ${cluster_network}
    RETURN    ${network}

Network - Delete VLAN Network
    [Arguments]    ${name}
    [Documentation]    Delete VLAN network.
    ...               Args:
    ...                   name: Network name
    Log    Deleting VLAN network: ${name}
    delete_vlan_network    ${name}

# IP Pool Operations
Network - Get IP Pool
    [Arguments]    ${name}
    [Documentation]    Get IP pool by name, returns None if not found.
    ...               Args:
    ...                   name: IP pool name
    ...               Returns:
    ...                   dict or None: IP pool data
    ${pool}=    get_ip_pool    ${name}
    RETURN    ${pool}

Network - Create IP Pool
    [Arguments]    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}
    [Documentation]    Create IP pool.
    ...               Args:
    ...                   name: IP pool name
    ...                   subnet: Subnet CIDR
    ...                   start_ip: Start IP address
    ...                   end_ip: End IP address
    ...                   network_id: Network ID
    ...               Returns:
    ...                   dict: IP pool data
    Log    Creating IP pool: ${name}
    ${pool}=    create_ip_pool    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}
    RETURN    ${pool}

Network - Delete IP Pool
    [Arguments]    ${name}
    [Documentation]    Delete IP pool.
    ...               Args:
    ...                   name: IP pool name
    Log    Deleting IP pool: ${name}
    delete_ip_pool    ${name}
