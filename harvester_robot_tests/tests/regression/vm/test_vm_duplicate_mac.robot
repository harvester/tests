*** Settings ***
Documentation    VM duplicate MAC address check across VM network changes
...    The VM webhook refuses a MAC address that another VM already uses on
...    the same cluster network. It used to skip that check when the VM's
...    interfaces were unchanged, so an edit that only moves a NIC to a VM
...    network on another cluster network (spec.template.spec.networks,
...    e.g. a KubeVirt LiveUpdateNADRef NAD swap) could create a duplicate
...    MAC (harvester/harvester#11769, fix harvester/harvester#11770).
...    The VMs are stopped and have no disks, and the cluster networks have
...    no uplink, so the suite only exercises admission and runs on any
...    cluster, including a single node.
Test Tags        virtualmachines    network    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/network.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Prefix of the generated resource names (cluster network names are at most 12 chars)
${NAME_PREFIX}    mac

# Dynamic Variables
${CN_A}         ${EMPTY}
${CN_B}         ${EMPTY}
${NET_A}        ${EMPTY}
${NET_B}        ${EMPTY}
${VM_A}         ${EMPTY}
${MAC}          ${EMPTY}
@{CREATED_VMS}
@{CREATED_NADS}
@{CREATED_CNS}


*** Test Cases ***
Reject Duplicate MAC On The Same Cluster Network
    [Tags]    p1    negative
    [Documentation]    Baseline: a new VM whose NIC reuses VM A's MAC on the same
    ...    cluster network is refused.
    ${vm}=    Tracked VM Name    dup
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_A}    mac=${MAC}
    # retried: the webhook reads VMs from its cache, which may not have VM A yet
    Wait Until Keyword Succeeds    30s    3s
    ...    VM Create Should Be Rejected    ${vm}    ${nic}    duplicate mac address

Allow The Same MAC On Another Cluster Network
    [Tags]    p1
    [Documentation]    MAC addresses are unique per cluster network, so the same MAC
    ...    on a VM network of another cluster network is accepted.
    ${vm}=    Tracked VM Name    other
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_B}    mac=${MAC}
    ${result}=    Try To Create VM With Bridge NICs    ${vm}    ${nic}
    Operation Should Succeed    ${result}
    # the MAC must be free on the other cluster network for the next cases
    VM is deleted    ${vm}

Reject Duplicate MAC When Only VM Networks Change
    [Tags]    p0    negative
    [Documentation]    harvester/harvester#11769: VM B uses VM A's MAC on another
    ...    cluster network. Moving VM B's NIC to VM A's cluster network by
    ...    changing only spec.template.spec.networks (interfaces untouched)
    ...    must be refused, and VM B must stay on its network.
    ${vm}=    Tracked VM Name    swap
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_B}    mac=${MAC}
    ${result}=    Try To Create VM With Bridge NICs    ${vm}    ${nic}
    Operation Should Succeed    ${result}
    ${result}=    Try To Change VM Networks    ${vm}    nic-1=${NET_A}
    Webhook Should Reject    ${result}    duplicate mac address
    VM Network Should Be    ${vm}    nic-1    ${NET_B}

Reject Duplicate MAC When Only The Interface MAC Changes
    [Tags]    p1    negative
    [Documentation]    Baseline for the interface path: changing a NIC's MAC to VM
    ...    A's MAC on the same cluster network is refused.
    ${vm}=    Tracked VM Name    newmac
    ${unique}=    Random MAC
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_A}    mac=${unique}
    ${result}=    Try To Create VM With Bridge NICs    ${vm}    ${nic}
    Operation Should Succeed    ${result}
    ${result}=    Try To Change VM Interface MACs    ${vm}    nic-1=${MAC}
    Webhook Should Reject    ${result}    duplicate mac address

Allow VM Network Change Without A Duplicate MAC
    [Tags]    p1
    [Documentation]    Re-running the check on a networks-only change must not refuse
    ...    a valid edit: a NIC with a unique MAC moves to VM A's cluster network.
    ${vm}=    Tracked VM Name    move
    ${unique}=    Random MAC
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_B}    mac=${unique}
    ${result}=    Try To Create VM With Bridge NICs    ${vm}    ${nic}
    Operation Should Succeed    ${result}
    ${result}=    Try To Change VM Networks    ${vm}    nic-1=${NET_A}
    Operation Should Succeed    ${result}
    VM Network Should Be    ${vm}    nic-1    ${NET_A}


*** Keywords ***
Local Suite Setup
    Set up test environment
    ${hex}=    Evaluate    secrets.token_hex(3)    modules=secrets
    # cluster network names: <prefix>-<6 hex><a|b>, at most 12 chars
    Set Suite Variable    ${CN_A}    ${NAME_PREFIX}-${hex}a
    Set Suite Variable    ${CN_B}    ${NAME_PREFIX}-${hex}b
    FOR    ${cn}    IN    ${CN_A}    ${CN_B}
        Append To List    ${CREATED_CNS}    ${cn}
        Create Cluster Network    ${cn}
        Append To List    ${CREATED_NADS}    ${cn}-vlan100
        Create VLAN Network    ${cn}-vlan100    100    ${cn}
    END
    Set Suite Variable    ${NET_A}    default/${CN_A}-vlan100
    Set Suite Variable    ${NET_B}    default/${CN_B}-vlan100
    ${mac}=    Random MAC
    Set Suite Variable    ${MAC}    ${mac}
    ${vm}=    Tracked VM Name    a
    Set Suite Variable    ${VM_A}    ${vm}
    ${nic}=    Create Dictionary    name=nic-1    network=${NET_A}    mac=${MAC}
    ${result}=    Try To Create VM With Bridge NICs    ${VM_A}    ${nic}
    Operation Should Succeed    ${result}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    # VMs first: a VM network can't be deleted while a VM uses it, and a
    # cluster network can't be deleted while it has VM networks
    FOR    ${vm}    IN    @{CREATED_VMS}
        Run Keyword And Ignore Error    VM is deleted    ${vm}
    END
    FOR    ${nad}    IN    @{CREATED_NADS}
        Run Keyword And Ignore Error    Delete VLAN Network    ${nad}
    END
    FOR    ${cn}    IN    @{CREATED_CNS}
        Run Keyword And Ignore Error    Wait Until Keyword Succeeds    60s    5s
        ...    Delete Cluster Network    ${cn}
    END

Tracked VM Name
    [Arguments]    ${role}
    [Documentation]    Return a unique VM name and record it for cleanup.
    ${name}=    Generate Unique Name    ${NAME_PREFIX}    ${role}
    Append To List    ${CREATED_VMS}    ${name}
    RETURN    ${name}

Random MAC
    [Documentation]    A random locally administered unicast MAC address.
    ${mac}=    Evaluate    "02:" + ":".join("%02x" % b for b in secrets.token_bytes(5))    modules=secrets
    RETURN    ${mac}

Operation Should Succeed
    [Arguments]    ${result}
    Should Be True    ${result}[success]
    ...    msg=Operation was rejected (code=${result}[code]): ${result}[message]

VM Create Should Be Rejected
    [Arguments]    ${vm_name}    ${nic}    @{expected_messages}
    ${result}=    Try To Create VM With Bridge NICs    ${vm_name}    ${nic}
    IF    ${result}[success]
        # created before the webhook cache had VM A: remove it before retrying
        VM is deleted    ${vm_name}
    END
    Webhook Should Reject    ${result}    @{expected_messages}

Webhook Should Reject
    [Arguments]    ${result}    @{expected_messages}
    [Documentation]    Assert a {success, code, message} result was rejected. The VM
    ...    webhook reports the duplicate MAC denial as InternalError (500), so
    ...    any error code is accepted; the message must contain at least one
    ...    of expected_messages (case-insensitive).
    Should Not Be True    ${result}[success]
    ...    msg=Operation was expected to be rejected but succeeded (code=${result}[code])
    ${msg_lower}=    Convert To Lower Case    ${result}[message]
    ${lowered}=    Evaluate    [m.lower() for m in $expected_messages]
    Should Contain Any    ${msg_lower}    @{lowered}
    ...    msg=Expected message to contain one of ${expected_messages}, got: ${result}[message]
