*** Settings ***
Documentation    VlanConfig isolated uplink mode: API and webhook rules
...    harvester/harvester#11993 (HEP harvester/harvester#12031): a VlanConfig
...    with spec.uplink.mode=isolated attaches every NIC to <cn>-br as an
...    isolated bridge port (no bond), for switchless full-mesh networks
...    (harvester/network-controller-harvester#445).
...    These cases only cover the API and admission rules, so they run on any
...    cluster, including a single node:
...    - VlanConfigs are created as server-side dry runs, or with a node
...      selector that matches no node, so no agent ever touches a NIC and the
...      NIC names need not exist;
...    - every create uses strict field validation, so an API server without
...      the field rejects spec.uplink.mode instead of silently dropping it.
...    The data path (isolated bridge ports, no loop, storage/migration
...    traffic over the mesh) needs a 3-node direct-cabled mesh and is not
...    covered here.
Test Tags        network    vlanconfig    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/network.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Setup        Local Test Setup
Test Teardown     Local Test Teardown


*** Variables ***
# Prefix of the generated resource names (cluster network names are at most 12 chars)
${NAME_PREFIX}    iso
@{MESH_NICS}      mesh-nic0    mesh-nic1
# A node selector that matches no node: the VlanConfig is stored and admitted,
# but no node agent applies it
&{NO_NODE}        harvesterhci.io/robot-no-such-node=true

# Dynamic Variables
${CN}           ${EMPTY}
@{TEST_VCS}
@{TEST_NADS}


*** Test Cases ***
Accept Isolated Uplink Mode
    [Tags]    p0
    [Documentation]    A VlanConfig with uplink.mode=isolated, two NICs and MTU 9000
    ...    is accepted and keeps the mode (it is not pruned as an unknown field).
    ${result}=    Try To Create VLAN Config    ${CN}-vc    ${CN}    ${MESH_NICS}
    ...    mode=isolated    mtu=9000    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Succeed    ${result}
    Should Be Equal    ${result}[object][spec][uplink][mode]    isolated

Accept Explicit Bond Uplink Mode
    [Tags]    p1
    [Documentation]    uplink.mode=bond is the explicit form of today's default.
    ${result}=    Try To Create VLAN Config    ${CN}-vc    ${CN}    ${MESH_NICS}
    ...    mode=bond    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Succeed    ${result}
    Should Be Equal    ${result}[object][spec][uplink][mode]    bond

Reject Unknown Uplink Mode
    [Tags]    p1    negative
    [Documentation]    The CRD only allows "", bond and isolated.
    ${result}=    Try To Create VLAN Config    ${CN}-vc    ${CN}    ${MESH_NICS}
    ...    mode=mesh    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    Unsupported value    unknown uplink mode

Reject Isolated Uplink Mode Without NICs
    [Tags]    p1    negative
    [Documentation]    Isolated mode attaches each NIC to the bridge, so it needs at
    ...    least one NIC.
    @{no_nics}=    Create List
    ${result}=    Try To Create VLAN Config    ${CN}-vc    ${CN}    ${no_nics}
    ...    mode=isolated    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    requires at least one NIC

Reject Isolated Uplink Mode With Hardware Address
    [Tags]    p1    negative
    [Documentation]    In isolated mode each NIC keeps its own MAC address, so
    ...    linkAttributes.hardwareAddr is refused.
    # hardwareAddr is a base64 "byte" field: 02:00:00:00:00:01
    ${result}=    Try To Create VLAN Config    ${CN}-vc    ${CN}    ${MESH_NICS}
    ...    mode=isolated    hardware_addr=AgAAAAAB    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    hardwareAddr

Reject Mixed Uplink Modes On One Cluster Network
    [Tags]    p0    negative
    [Documentation]    All VlanConfigs of a cluster network must use the same mode:
    ...    with a bond VlanConfig stored, an isolated one is refused.
    Stored VLAN Config Is Created    ${CN}-bond    ${CN}    bond
    ${result}=    Try To Create VLAN Config    ${CN}-iso    ${CN}    ${MESH_NICS}
    ...    mode=isolated    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    must use the same mode

Reject Isolated Mode While A VM Network Uses The Cluster Network
    [Tags]    p0    negative
    [Documentation]    A cluster network can only become isolated when it carries
    ...    nothing but the storage, RWX and VM migration networks: with a VM
    ...    (VLAN) network on it, an isolated VlanConfig is refused.
    ${nad}=    Set Variable    ${CN}-vlan100
    Append To List    ${TEST_NADS}    ${nad}
    ${result}=    Try To Create VLAN Network    ${nad}    100    ${CN}
    Network Operation Should Succeed    ${result}
    ${result}=    Try To Create VLAN Config    ${CN}-iso    ${CN}    ${MESH_NICS}
    ...    mode=isolated    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    reserved for the storage, RWX and VM migration networks

Reject VM Network And Host Network On Isolated Cluster Network
    [Tags]    p0    negative
    [Documentation]    An isolated cluster network relays nothing between nodes, so a
    ...    VM (VLAN) network and a HostNetworkConfig on it are refused, and so
    ...    is a bond VlanConfig.
    Stored VLAN Config Is Created    ${CN}-iso    ${CN}    isolated
    ${result}=    Try To Create VLAN Network    ${CN}-vlan100    100    ${CN}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    uses isolated uplinks
    ${result}=    Try To Create Host Network Config    ${CN}-hnc    ${CN}    100    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    uses isolated uplinks
    ${result}=    Try To Create VLAN Config    ${CN}-bond    ${CN}    ${MESH_NICS}
    ...    mode=bond    node_selector=${NO_NODE}    dry_run=${True}
    Network Operation Should Be Rejected    ${result}    must use the same mode


*** Keywords ***
Local Suite Setup
    Set up test environment

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables

Local Test Setup
    # each case gets its own cluster network: <prefix>-<6 hex>, at most 12 chars
    ${hex}=    Evaluate    secrets.token_hex(3)    modules=secrets
    ${name}=    Set Variable    ${NAME_PREFIX}-${hex}
    Create Cluster Network    ${name}
    Set Test Variable    ${CN}    ${name}

Local Test Teardown
    Common Test Teardown
    FOR    ${nad}    IN    @{TEST_NADS}
        Run Keyword And Ignore Error    Delete VLAN Network    ${nad}
    END
    FOR    ${vc}    IN    @{TEST_VCS}
        Run Keyword And Ignore Error    Delete VLAN Config    ${vc}
    END
    # the cluster network can only go once its VlanConfigs and NADs are gone
    Wait Until Keyword Succeeds    60s    5s    Cluster Network Is Deleted    ${CN}
    Set Test Variable    @{TEST_NADS}
    Set Test Variable    @{TEST_VCS}

Cluster Network Is Deleted
    [Arguments]    ${name}
    Delete Cluster Network    ${name}

Stored VLAN Config Is Created
    [Arguments]    ${name}    ${cluster_network}    ${mode}
    [Documentation]    Store a VlanConfig that matches no node, so its uplink mode
    ...    counts for the cluster network but no NIC is touched.
    Append To List    ${TEST_VCS}    ${name}
    ${result}=    Try To Create VLAN Config    ${name}    ${cluster_network}    ${MESH_NICS}
    ...    mode=${mode}    node_selector=${NO_NODE}
    Network Operation Should Succeed    ${result}
