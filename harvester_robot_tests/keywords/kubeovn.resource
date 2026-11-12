*** Settings ***
Documentation    Kube-OVN (kubeovn-operator addon) Keywords - placement of the
...              ovn-central NB/SB raft members and the OVN DB addresses the
...              operator renders from its Configuration.
Library          ../libs/keywords/kubeovn_keywords.py
Library          ../libs/keywords/addon_keywords.py
Resource         variables.resource
Resource         common.resource


*** Variables ***
${KUBEOVN_ADDON_NAME}               kubeovn-operator
${OVN_CENTRAL_SELECTOR}             app=ovn-central
${KUBE_OVN_CONTROLLER_SELECTOR}     app=kube-ovn-controller


*** Keywords ***
Kube-OVN Addon Should Be Enabled
    [Documentation]    Skip the calling suite when the kubeovn-operator addon is
    ...    not enabled; the suite never enables addons on its own.
    ${enabled}=    addon_keywords.is_addon_enabled    ${KUBEOVN_ADDON_NAME}
    Skip If    not ${enabled}    The ${KUBEOVN_ADDON_NAME} addon is not enabled on this cluster
    ${exists}=    kubeovn_keywords.configuration_exists
    Skip If    not ${exists}    The kube-ovn Configuration has not been created yet

Get Master Nodes Label
    ${label}=    kubeovn_keywords.get_master_nodes_label
    RETURN    ${label}

Get OVN Central Nodes Label
    ${label}=    kubeovn_keywords.get_ovn_central_nodes_label
    RETURN    ${label}

Set OVN Central Nodes Label
    [Arguments]    ${label}
    [Documentation]    Set spec.ovnCentral.nodesLabel; an empty label removes it.
    kubeovn_keywords.set_ovn_central_nodes_label    ${label}

OVN Central Nodes Label Should Be
    [Arguments]    ${expected}
    kubeovn_keywords.ovn_central_nodes_label_should_be    ${expected}

Get Node IPs Matching Label
    [Arguments]    ${label}
    ${ips}=    kubeovn_keywords.get_node_ips_matching_label    ${label}
    RETURN    ${ips}

Get Node Names Matching Label
    [Arguments]    ${label}
    ${names}=    kubeovn_keywords.get_node_names_matching_label    ${label}
    RETURN    ${names}

Get Witness Node Names
    ${names}=    kubeovn_keywords.get_witness_node_names
    RETURN    ${names}

Configuration Status Should List OVN Central Nodes
    [Arguments]    ${expected_ips}
    kubeovn_keywords.wait_for_ovn_central_node_addresses    ${expected_ips}

Configuration Status Should List Master Nodes
    [Arguments]    ${expected_ips}
    kubeovn_keywords.wait_for_ovn_central_node_addresses    ${expected_ips}
    ...    field=matchingNodeAddresses

OVN Central Should Target Nodes
    [Arguments]    ${label}    ${expected_ips}
    [Documentation]    ovn-central renders one replica per raft member, a
    ...    required node affinity for ${label} and NODE_IPS listing every member.
    kubeovn_keywords.ovn_central_should_target_nodes    ${label}    ${expected_ips}

OVN Clients Should Use Raft Members
    [Arguments]    ${expected_ips}
    [Documentation]    Every OVN client is handed all raft members in OVN_DB_IPS.
    kubeovn_keywords.ovn_db_ips_should_be    Deployment    kube-ovn-controller
    ...    kube-ovn-controller    ${expected_ips}
    kubeovn_keywords.ovn_db_ips_should_be    DaemonSet    ovs-ovn    openvswitch    ${expected_ips}

OVN Central Pods Should Run Only On Nodes
    [Arguments]    ${node_names}
    kubeovn_keywords.pods_should_run_only_on_nodes    ${OVN_CENTRAL_SELECTOR}    ${node_names}

Kube-OVN Controller Should Run Only On Nodes
    [Arguments]    ${node_names}
    [Documentation]    kube-ovn-controller keeps following masterNodesLabel:
    ...    one replica per master node, none Pending.
    ${count}=    Get Length    ${node_names}
    kubeovn_keywords.deployment_replicas_should_be    kube-ovn-controller    ${count}
    kubeovn_keywords.pods_should_run_only_on_nodes    ${KUBE_OVN_CONTROLLER_SELECTOR}    ${node_names}

Raft Members Should Be
    [Arguments]    ${expected_ips}
    [Documentation]    Both the NB and SB raft clusters list exactly the expected
    ...    members and have an elected leader.
    kubeovn_keywords.raft_members_should_be    OVN_Northbound    ${expected_ips}
    kubeovn_keywords.raft_members_should_be    OVN_Southbound    ${expected_ips}

Bootstrap Configuration OVN Central Should Have
    [Arguments]    ${key}    ${expected}
    ${ovn_central}=    kubeovn_keywords.get_bootstrap_ovn_central
    Dictionary Should Contain Key    ${ovn_central}    ${key}
    ...    msg=Bootstrap Configuration ovnCentral has no ${key}: ${ovn_central}
    Should Be Equal As Strings    ${ovn_central}[${key}]    ${expected}

Bootstrap OVN Central Should Tolerate Witness Taint
    kubeovn_keywords.bootstrap_ovn_central_should_tolerate_witness_taint
