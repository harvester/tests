*** Settings ***
Documentation    Host/Node Keywords
Library          Collections
Library          ../libs/keywords/common_keywords.py
Library          ../libs/keywords/host_keywords.py

*** Keywords ***
Get node ${node_id}
    ${node_name}=    get_node_by_index    ${node_id}
    RETURN    ${node_name}

Cluster has at least ${count} nodes
    [Documentation]    Verify cluster has minimum number of nodes
    ${node_count}=    get_node_count
    Should be true    ${node_count} >= ${count}    Cluster only has ${node_count} nodes, need at least ${count}

Power on node ${node_id}
    [Documentation]    Power on a node using external script
    ${node_name}=    get_node_by_index    ${node_id}
    ${node_ip}=      get_node_ip    ${node_name}
    power_on_node    ${node_name}    ${node_ip}

Power off node ${node_id}
    [Documentation]    Power off a node using external script
    ${node_name}=    get_node_by_index    ${node_id}
    ${node_ip}=      get_node_ip    ${node_name}
    power_off_node    ${node_name}    ${node_ip}

Reboot node ${node_id}
    [Documentation]    Reboot a node using external script
    ${node_name}=    get_node_by_index    ${node_id}
    ${node_ip}=      get_node_ip    ${node_name}
    reboot_node    ${node_name}    ${node_ip}

Wait for node ${node_id} ready
    [Documentation]    Wait for node to be in Ready state
    ${node_name}=    get_node_by_index    ${node_id}
    wait_for_node_ready    ${node_name}

Wait for node ${node_id} to be marked as down
    [Documentation]    Wait for node to be marked as NotReady
    ${node_name}=    get_node_by_index    ${node_id}
    wait_for_node_down    ${node_name}

Drain node ${node_id}
    [Documentation]    Drain workloads from node
    ${node_name}=    get_node_by_index    ${node_id}
    drain_node    ${node_name}

Uncordon node ${node_id}
    [Documentation]    Mark node as schedulable
    ${node_name}=    get_node_by_index    ${node_id}
    uncordon_node    ${node_name}

Cordon node ${node_id}
    [Documentation]    Mark node as unschedulable
    ${node_name}=    get_node_by_index    ${node_id}
    cordon_node    ${node_name}

Enable node ${node_id} scheduling
    [Documentation]    Enable scheduling on node
    ${node_name}=    get_node_by_index    ${node_id}
    enable_node_scheduling    ${node_name}

Disable node ${node_id} scheduling
    [Documentation]    Disable scheduling on node
    ${node_name}=    get_node_by_index    ${node_id}
    disable_node_scheduling    ${node_name}

Enable node ${node_id} default disk
    [Documentation]    Enable default disk on node
    ${node_name}=    get_node_by_index    ${node_id}
    enable_node_default_disk    ${node_name}

Disable node ${node_id} default disk
    [Documentation]    Disable default disk on node
    ${node_name}=    get_node_by_index    ${node_id}
    disable_node_default_disk    ${node_name}

Get node ${node_id} status
    [Documentation]    Get current status of node
    ${node_name}=    get_node_by_index    ${node_id}
    ${status}=       get_node_status    ${node_name}
    RETURN    ${status}

Node ${node_id} should be ready
    [Documentation]    Verify node is in Ready state
    ${node_name}=    get_node_by_index    ${node_id}
    ${status}=       get_node_status    ${node_name}
    Should be equal    ${status}    Ready    Node ${node_name} is not Ready

Node ${node_id} should be not ready
    [Documentation]    Verify node is not in Ready state
    ${node_name}=    get_node_by_index    ${node_id}
    ${status}=       get_node_status    ${node_name}
    Should not be equal    ${status}    Ready    Node ${node_name} is Ready

Record VM ${vm_id} current node
    [Documentation]    Store current node of VM for later comparison
    ${vm_name}=     generate_name_with_suffix    vm    ${vm_id}
    ${node_name}=   get_vm_node    ${vm_name}
    Set test variable    ${ORIGINAL_VM_NODE}    ${node_name}

Wait for VM ${vm_id} to migrate to different node
    [Documentation]    Wait for VM to migrate away from original node
    [Arguments]    ${timeout}=600
    ${vm_name}=    generate_name_with_suffix    vm    ${vm_id}
    wait_for_vm_migration_from_node    ${vm_name}    ${ORIGINAL_VM_NODE}    ${timeout}

Check VM ${vm_id} not on node ${node_id}
    [Documentation]    Verify VM is not running on specified node
    ${vm_name}=     generate_name_with_suffix    vm    ${vm_id}
    ${node_name}=   get_node_by_index    ${node_id}
    ${current_node}=    get_vm_node    ${vm_name}
    Should not be equal    ${current_node}    ${node_name}    VM ${vm_name} is still on node ${node_name}

Get healthy node names
    [Documentation]    Get list of all healthy (Ready) nodes
    ${node_names}=    get_healthy_nodes
    RETURN    ${node_names}

Cleanup test resources and restore nodes
    [Documentation]    Clean up resources and ensure all nodes are restored
    Cleanup test resources
    Restore all nodes
