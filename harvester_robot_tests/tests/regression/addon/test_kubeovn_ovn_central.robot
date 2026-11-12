*** Settings ***
Documentation    Kube-OVN ovn-central raft placement (harvester/harvester#12133)
...    The ovn-central NB/SB raft members can be placed on a dedicated node
...    label (spec.ovnCentral.nodesLabel, harvester/kubeovn-operator#93), and
...    Harvester bootstraps it with the etcd quorum label so a 2 management +
...    witness cluster gets a 3-member raft instead of a 2-member one with no
...    fault tolerance (harvester/charts#653). kube-ovn-controller and the
...    other control-plane components keep following masterNodesLabel.
...    Needs the kubeovn-operator addon enabled; the suite skips otherwise and
...    never enables it. Every case restores spec.ovnCentral.nodesLabel.
Test Tags        regression    addon    kubeovn    ovn-central

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/kubeovn.resource

Suite Setup      Local Suite Setup
Test Teardown    Common Test Teardown


*** Variables ***
# Label selecting the raft members; Harvester's intended value is the etcd
# quorum set (3 nodes => 3, 2 management + witness => 3, single node => 1).
${OVN_CENTRAL_NODES_LABEL}      %{OVN_CENTRAL_NODES_LABEL=node-role.kubernetes.io/etcd=true}

# Dynamic Variables
${MASTER_NODES_LABEL}           ${EMPTY}
${ORIGINAL_NODES_LABEL}         ${EMPTY}


*** Test Cases ***
OVN Central Raft Members Default To Master Nodes
    [Tags]    p1
    [Documentation]    With spec.ovnCentral.nodesLabel unset the placement is
    ...    unchanged from previous releases: ovn-central runs one raft member
    ...    on every node matching masterNodesLabel and OVN clients get exactly
    ...    those addresses.
    Skip If    "${ORIGINAL_NODES_LABEL}"
    ...    spec.ovnCentral.nodesLabel is already set to ${ORIGINAL_NODES_LABEL}
    ${ips}=      Get Node IPs Matching Label      ${MASTER_NODES_LABEL}
    ${nodes}=    Get Node Names Matching Label    ${MASTER_NODES_LABEL}
    Configuration Status Should List Master Nodes    ${ips}
    OVN Central Should Target Nodes    ${MASTER_NODES_LABEL}    ${ips}
    OVN Central Pods Should Run Only On Nodes    ${nodes}
    OVN Clients Should Use Raft Members    ${ips}
    Raft Members Should Be    ${ips}

OVN Central Raft Members Follow Dedicated Nodes Label
    [Tags]    p0
    [Documentation]    Setting spec.ovnCentral.nodesLabel moves the raft members
    ...    to the labelled nodes: the operator reports their addresses in
    ...    status.ovnCentralNodeAddresses, ovn-central renders one replica per
    ...    labelled node with a matching required node affinity and NODE_IPS,
    ...    every OVN client gets all members in OVN_DB_IPS, and the NB and SB
    ...    rafts converge on those members with a leader. kube-ovn-controller
    ...    stays on the masterNodesLabel nodes with no Pending replica.
    ${ips}=      Get Node IPs Matching Label      ${OVN_CENTRAL_NODES_LABEL}
    ${nodes}=    Get Node Names Matching Label    ${OVN_CENTRAL_NODES_LABEL}
    ${masters}=    Get Node Names Matching Label    ${MASTER_NODES_LABEL}
    Should Not Be Empty    ${nodes}    msg=No node matches ${OVN_CENTRAL_NODES_LABEL}
    Set OVN Central Nodes Label    ${OVN_CENTRAL_NODES_LABEL}
    OVN Central Nodes Label Should Be    ${OVN_CENTRAL_NODES_LABEL}
    Configuration Status Should List OVN Central Nodes    ${ips}
    OVN Central Should Target Nodes    ${OVN_CENTRAL_NODES_LABEL}    ${ips}
    OVN Central Pods Should Run Only On Nodes    ${nodes}
    OVN Clients Should Use Raft Members    ${ips}
    Kube-OVN Controller Should Run Only On Nodes    ${masters}
    Raft Members Should Be    ${ips}
    [Teardown]    Restore OVN Central Nodes Label

OVN Central Honours A Key-Only Nodes Label
    [Tags]    p2
    [Documentation]    nodesLabel also accepts a bare label key; ovn-central then
    ...    requires the key to exist (operator Exists) on its nodes.
    ${key}=    Evaluate    $OVN_CENTRAL_NODES_LABEL.split("=", 1)[0]
    ${ips}=      Get Node IPs Matching Label      ${key}
    ${nodes}=    Get Node Names Matching Label    ${key}
    Set OVN Central Nodes Label    ${key}
    OVN Central Nodes Label Should Be    ${key}
    Configuration Status Should List OVN Central Nodes    ${ips}
    OVN Central Should Target Nodes    ${key}    ${ips}
    OVN Central Pods Should Run Only On Nodes    ${nodes}
    Raft Members Should Be    ${ips}
    [Teardown]    Restore OVN Central Nodes Label

Witness Node Joins The OVN Central Raft
    [Tags]    p0    witness
    [Documentation]    The bug scenario: on a 2 management + witness cluster the
    ...    etcd quorum label makes the witness the third raft member. The
    ...    ovn-central replica on the (NoExecute tainted) witness must be
    ...    Running, while kube-ovn-controller is not scheduled there and has
    ...    no Pending replica. Needs a witness node; skipped otherwise.
    ${witnesses}=    Get Witness Node Names
    Skip If    not ${witnesses}    No witness node (etcd but not control-plane) in this cluster
    ${etcd_label}=    Set Variable    node-role.kubernetes.io/etcd=true
    ${ips}=      Get Node IPs Matching Label      ${etcd_label}
    ${nodes}=    Get Node Names Matching Label    ${etcd_label}
    ${masters}=    Get Node Names Matching Label    ${MASTER_NODES_LABEL}
    Set OVN Central Nodes Label    ${etcd_label}
    Configuration Status Should List OVN Central Nodes    ${ips}
    OVN Central Pods Should Run Only On Nodes    ${nodes}
    Kube-OVN Controller Should Run Only On Nodes    ${masters}
    Raft Members Should Be    ${ips}
    [Teardown]    Restore OVN Central Nodes Label

Bootstrap Configuration Places OVN Central On Etcd Quorum
    [Tags]    p1    charts
    [Documentation]    New installs get the etcd quorum label from the bootstrap
    ...    ConfigMap the operator creates its Configuration from
    ...    (harvester/charts#653), with the default tolerations that let the
    ...    member on a tainted witness schedule.
    Bootstrap Configuration OVN Central Should Have
    ...    nodesLabel    node-role.kubernetes.io/etcd=true
    Bootstrap OVN Central Should Tolerate Witness Taint


*** Keywords ***
Local Suite Setup
    Set up test environment
    Kube-OVN Addon Should Be Enabled
    ${master}=    Get Master Nodes Label
    Set Suite Variable    ${MASTER_NODES_LABEL}    ${master}
    ${original}=    Get OVN Central Nodes Label
    Set Suite Variable    ${ORIGINAL_NODES_LABEL}    ${original}

Restore OVN Central Nodes Label
    [Documentation]    Put spec.ovnCentral.nodesLabel back and wait until the
    ...    raft converges on the original members again.
    IF    "${TEST STATUS}" == "SKIP"    RETURN
    Run Keyword If Test Failed    Log Variables
    Set OVN Central Nodes Label    ${ORIGINAL_NODES_LABEL}
    ${label}=    Set Variable If    "${ORIGINAL_NODES_LABEL}"
    ...    ${ORIGINAL_NODES_LABEL}    ${MASTER_NODES_LABEL}
    ${ips}=    Get Node IPs Matching Label    ${label}
    Run Keyword And Continue On Failure    Raft Members Should Be    ${ips}
