*** Settings ***
Documentation    NetworkAttachmentDefinition webhook: non-bridge CNI types
...    harvester/harvester#11990 (needed by #11989, Longhorn on an RDMA NIC):
...    the network webhook treated every NAD that is not kube-ovn as a bridge
...    NAD and rejected ipvlan, macvlan, host-device and SR-IOV NADs with
...    "the length of bridge name is less than 3". After the fix
...    (harvester/network-controller-harvester#444) those NADs are accepted
...    and stored unmodified, their route annotation and CNI type are still
...    validated, and bridge NADs are validated as before.
...    No VM is attached, so the NIC names in the configs need not exist.
Test Tags        network    nad    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/network.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Prefix of the generated resource names
${NAME_PREFIX}    nad
${ROUTE_ANNOTATION}    network.harvesterhci.io/route
${SRIOV_RESOURCE_ANNOTATION}    k8s.v1.cni.cncf.io/resourceName

# Dynamic Variables
${SUFFIX}       ${EMPTY}
@{CREATED_NADS}


*** Test Cases ***
Create Macvlan NAD
    [Tags]    p0
    [Documentation]    A macvlan NAD must be accepted and stored unmodified.
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=macvlan
    ...    master=eth1    mode=bridge    ipam=${{ {} }}
    Non-Bridge NAD Should Be Accepted    macvlan    ${config}

Create Ipvlan NAD
    [Tags]    p0
    [Documentation]    An ipvlan NAD (with whereabouts IPAM) must be accepted and
    ...    stored unmodified.
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=ipvlan
    ...    master=eth1    mode=l2
    ...    ipam=${{ {"type": "whereabouts", "range": "10.99.0.0/24"} }}
    Non-Bridge NAD Should Be Accepted    ipvlan    ${config}

Create Host-Device NAD
    [Tags]    p1
    [Documentation]    A host-device NAD must be accepted and stored unmodified.
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=host-device
    ...    device=eth2    ipam=${{ {} }}
    Non-Bridge NAD Should Be Accepted    hostdev    ${config}

Create SR-IOV NAD
    [Tags]    p1
    [Documentation]    An SR-IOV NAD bound to a device plugin resource must be
    ...    accepted and stored unmodified.
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=sriov
    ...    vlan=${0}    ipam=${{ {} }}
    ${annotations}=    Create Dictionary    ${SRIOV_RESOURCE_ANNOTATION}=intel.com/sriov_netdevice
    Non-Bridge NAD Should Be Accepted    sriov    ${config}    annotations=${annotations}

Update Non-Bridge NAD Config But Not Its CNI Type
    [Tags]    p1
    [Documentation]    The config of a non-bridge NAD can be changed (here the IPAM
    ...    range), but its CNI type stays immutable.
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=ipvlan
    ...    master=eth1    mode=l2
    ...    ipam=${{ {"type": "whereabouts", "range": "10.99.0.0/24"} }}
    ${name}=    Non-Bridge NAD Should Be Accepted    ipvlan-upd    ${config}
    ${changed}=    Copy Dictionary    ${config}
    Set To Dictionary    ${changed}    ipam=${{ {"type": "whereabouts", "range": "10.98.0.0/24"} }}
    ${result}=    Try To Update NAD Config    ${name}    ${changed}
    NAD Operation Should Succeed    ${result}
    NAD Config Should Be Stored Unmodified    ${name}    ${changed}
    ${retyped}=    Copy Dictionary    ${changed}
    Set To Dictionary    ${retyped}    type=macvlan    mode=bridge
    ${result}=    Try To Update NAD Config    ${name}    ${retyped}
    NAD Operation Should Be Rejected    ${result}    cannot be updated from network type
    NAD Config Should Be Stored Unmodified    ${name}    ${changed}

Reject Non-Bridge NAD With Invalid Route Annotation
    [Tags]    p1    negative
    [Documentation]    The route annotation of a non-bridge NAD is still validated:
    ...    an unknown route mode must be rejected for that reason (not for a
    ...    missing bridge name).
    ${config}=    Create Dictionary    cniVersion=0.3.1    type=macvlan
    ...    master=eth1    mode=bridge    ipam=${{ {} }}
    ${annotations}=    Create Dictionary    ${ROUTE_ANNOTATION}={"mode":"bogus"}
    ${result}=    Try To Create Tracked NAD    macvlan-route    ${config}    annotations=${annotations}
    NAD Operation Should Be Rejected    ${result}    unknown mode bogus

Reject Bridge NAD On Missing Cluster Network
    [Tags]    p0    negative
    [Documentation]    Bridge NADs keep the cluster network checks: a VLAN NAD whose
    ...    cluster network does not exist must be rejected.
    ${cn}=    Set Variable    missing-cn
    ${config}=    Create Dictionary    cniVersion=0.3.1    name=br-missing-${SUFFIX}
    ...    type=bridge    bridge=${cn}-br    promiscMode=${True}    vlan=${200}    ipam=${{ {} }}
    ${labels}=    Create Dictionary    network.harvesterhci.io/clusternetwork=${cn}
    ...    network.harvesterhci.io/type=L2VlanNetwork
    ${result}=    Try To Create Tracked NAD    br-missing    ${config}    labels=${labels}
    NAD Operation Should Be Rejected    ${result}    not found

Reject Bridge NAD With Too Short Bridge Name
    [Tags]    p1    negative
    [Documentation]    Bridge NADs keep the bridge name check: a bridge name shorter
    ...    than 3 characters must still be rejected.
    ${config}=    Create Dictionary    cniVersion=0.3.1    name=br-short-${SUFFIX}
    ...    type=bridge    bridge=br    promiscMode=${True}    vlan=${200}    ipam=${{ {} }}
    ${result}=    Try To Create Tracked NAD    br-short    ${config}
    NAD Operation Should Be Rejected    ${result}    length of bridge name


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${NAME_PREFIX}
    Set Suite Variable    ${SUFFIX}    ${suffix}
    Set up test environment

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    FOR    ${nad}    IN    @{CREATED_NADS}
        Run Keyword And Ignore Error    Delete VLAN Network    ${nad}
    END

Try To Create Tracked NAD
    [Arguments]    ${prefix}    ${config}    ${labels}=${None}    ${annotations}=${None}
    [Documentation]    Try to create NAD <prefix>-<suffix> and record it for cleanup
    ...    (also when it should have been rejected but was not).
    ${name}=    Set Variable    ${prefix}-${SUFFIX}
    Append To List    ${CREATED_NADS}    ${name}
    ${result}=    Try To Create NAD    ${name}    ${config}    ${labels}    ${annotations}
    RETURN    ${result}

Non-Bridge NAD Should Be Accepted
    [Arguments]    ${prefix}    ${config}    ${labels}=${None}    ${annotations}=${None}
    [Documentation]    Create a non-bridge NAD; it must be accepted and stored as sent.
    ...    On a webhook without the fix the create is rejected with
    ...    "the length of bridge name is less than 3".
    ${result}=    Try To Create Tracked NAD    ${prefix}    ${config}    ${labels}    ${annotations}
    NAD Operation Should Succeed    ${result}
    NAD Config Should Be Stored Unmodified    ${prefix}-${SUFFIX}    ${config}
    RETURN    ${prefix}-${SUFFIX}
