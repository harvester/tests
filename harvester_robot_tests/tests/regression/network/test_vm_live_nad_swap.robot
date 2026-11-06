*** Settings ***
Documentation    Change the VM network (NAD) of a running VM without a restart
...    harvester/harvester#11769: KubeVirt v1.9 (Harvester v1.10) applies a
...    change of only spec.template.spec.networks[].multus.networkName of a
...    running VM through LiveUpdateNADRef: no RestartRequired, the NAD is
...    synced into the VMI with MigrationRequired=True
...    (AutoMigrationDueToLiveUpdate), and the workload updater live-migrates
...    the VMI to a virt-launcher pod attached to the new NAD. The MAC address
...    and guest interface name are kept.
...    Harvester already sets the prerequisites (vmRolloutStrategy LiveUpdate,
...    workloadUpdateMethods [LiveMigrate]).
...    Requirements:
...    - Harvester v1.10.0 or newer (KubeVirt v1.9), at least two nodes;
...    - a VM image (NAD_SWAP_IMAGE, "<image name>" in the default namespace)
...      on a migratable storage class, or the suite imports UBUNTU_IMAGE_URL;
...    - two bridge VLAN networks on the same cluster network
...      (NAD_SWAP_SOURCE_NETWORK / NAD_SWAP_TARGET_NETWORK, "<ns>/<nad>"),
...      or the suite creates them with VLAN_ID and VLAN_ID+1 on CLUSTER_NETWORK;
...    - an overlay (Kube-OVN) VM network for the bridge -> overlay case
...      (NAD_SWAP_OVERLAY_NETWORK, or the first OverlayNetwork NAD found);
...      that case is skipped when there is none;
...    - two overlay VM networks with Kube-OVN subnets for the overlay ->
...      overlay case (NAD_SWAP_OVERLAY_NETWORK / NAD_SWAP_OVERLAY_TARGET_NETWORK);
...      that case is skipped unless both are set.
...    Test VMs only have bridge NICs with fixed MAC addresses, and cloud-init
...    turns DHCP off on them, so they never send DHCP requests on the VLANs.
...    The duplicate MAC case needs the VM webhook fix from
...    harvester/harvester#11770; exclude it with `-e requires-11770` on
...    builds without it.
Test Tags        network    virtualmachines    live-nad-swap    issue-11769

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/network.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Local Test Teardown


*** Variables ***
${IMAGE_ID}             %{NAD_SWAP_IMAGE=}
${SOURCE_NETWORK}       %{NAD_SWAP_SOURCE_NETWORK=}
${TARGET_NETWORK}       %{NAD_SWAP_TARGET_NETWORK=}
${OVERLAY_NETWORK}      %{NAD_SWAP_OVERLAY_NETWORK=}
# overlay -> overlay case only, both need a Kube-OVN subnet: no auto-discovery
${OVERLAY_SOURCE_NETWORK}    %{NAD_SWAP_OVERLAY_NETWORK=}
${OVERLAY_TARGET_NETWORK}    %{NAD_SWAP_OVERLAY_TARGET_NETWORK=}
${CLUSTER_NETWORK}      %{CLUSTER_NETWORK=mgmt}
${NIC}                  nic-1
# small test VMs: 1 vCPU, 2Gi memory, 4Gi boot disk
&{VM_CONFIG}            disk_size=4Gi    requests_memory=1365Mi

# Dynamic Variables
${SUFFIX}               ${EMPTY}
${SUITE_IMAGE}          ${EMPTY}
${DUP_CN}               ${EMPTY}
@{SUITE_NADS}


*** Test Cases ***
Live Swap VM Network Between Bridge VLAN Networks
    [Tags]    p0
    [Documentation]    Change only the NAD of the bridge NIC of a running,
    ...    live-migratable VM to another VLAN network on the same cluster
    ...    network. KubeVirt must apply it with a workload update migration
    ...    instead of asking for a restart, and keep the MAC address.
    ${vm}=    Set Variable    nsw-live-${SUFFIX}
    ${mac}=    Generate MAC Address
    Given VM is created with bridge NIC    ${vm}    ${IMAGE_ID}    ${SOURCE_NETWORK}    ${mac}    &{VM_CONFIG}
    And VM should be running    ${vm}
    And VM condition should be    ${vm}    LiveMigratable    True
    And VM launcher pod should be attached to network    ${vm}    ${SOURCE_NETWORK}    ${mac}
    ${known}=    Get VM migrations    ${vm}

    When VM network is changed    ${vm}    ${NIC}    ${TARGET_NETWORK}

    ${migration}=    Then VM workload update migration should be created    ${vm}    ${known}
    And VM migration should succeed    ${migration}
    And VM should be running    ${vm}
    And VM should not have condition    ${vm}    RestartRequired
    And VMI network should be    ${vm}    ${NIC}    ${TARGET_NETWORK}
    And VMI interface MAC should be    ${vm}    ${NIC}    ${mac}
    And VM launcher pod should be attached to network    ${vm}    ${TARGET_NETWORK}    ${mac}
    And VM launcher pod should not be attached to network    ${vm}    ${SOURCE_NETWORK}

Live Swap VM Network Between Overlay Networks
    [Tags]    p1
    [Documentation]    Change only the NAD of the overlay NIC of a running,
    ...    live-migratable VM to another overlay (Kube-OVN) network. The
    ...    binding stays managedtap, so KubeVirt must apply it with a
    ...    workload update migration instead of asking for a restart, and
    ...    keep the MAC address. Kube-OVN gives the target pod an address on
    ...    the new subnet; the guest only uses it after a new DHCP request,
    ...    which is not checked here (test VMs have DHCP off).
    ...    Both overlay networks need a Kube-OVN subnet, so this case only
    ...    runs when NAD_SWAP_OVERLAY_NETWORK and
    ...    NAD_SWAP_OVERLAY_TARGET_NETWORK are set.
    Skip If    '${OVERLAY_SOURCE_NETWORK}' == '${EMPTY}' or '${OVERLAY_TARGET_NETWORK}' == '${EMPTY}'
    ...    NAD_SWAP_OVERLAY_NETWORK and NAD_SWAP_OVERLAY_TARGET_NETWORK are not set
    ${vm}=    Set Variable    nsw-o2o-${SUFFIX}
    ${mac}=    Generate MAC Address
    Given VM is created with bridge NIC    ${vm}    ${IMAGE_ID}    ${OVERLAY_SOURCE_NETWORK}    ${mac}    &{VM_CONFIG}
    And VM should be running    ${vm}
    And VM condition should be    ${vm}    LiveMigratable    True
    ${mac_before}=    Get VMI interface MAC    ${vm}    ${NIC}
    ${known}=    Get VM migrations    ${vm}

    When VM network is changed    ${vm}    ${NIC}    ${OVERLAY_TARGET_NETWORK}

    ${migration}=    Then VM workload update migration should be created    ${vm}    ${known}
    And VM migration should succeed    ${migration}
    And VM should be running    ${vm}
    And VM should not have condition    ${vm}    RestartRequired
    And VMI network should be    ${vm}    ${NIC}    ${OVERLAY_TARGET_NETWORK}
    And VMI interface MAC should be    ${vm}    ${NIC}    ${mac_before}
    And VM launcher pod should not be attached to network    ${vm}    ${OVERLAY_SOURCE_NETWORK}

Swap VM Network From Bridge To Overlay Requires Restart
    [Tags]    p2
    [Documentation]    Out of scope for LiveUpdateNADRef: moving a bridge NIC
    ...    to an overlay (Kube-OVN) network also changes the binding (the
    ...    Harvester mutator switches bridge to managedtap), so the VM must
    ...    get RestartRequired. KubeVirt still syncs the NAD into the VMI and
    ...    starts a workload update migration; that migration is not checked
    ...    here, the change is only complete after a restart.
    Skip If    '${OVERLAY_NETWORK}' == '${EMPTY}'    No overlay (OverlayNetwork) VM network available
    ${vm}=    Set Variable    nsw-ovl-${SUFFIX}
    ${mac}=    Generate MAC Address
    Given VM is created with bridge NIC    ${vm}    ${IMAGE_ID}    ${SOURCE_NETWORK}    ${mac}    &{VM_CONFIG}
    And VM should be running    ${vm}

    When VM network is changed    ${vm}    ${NIC}    ${OVERLAY_NETWORK}

    Then VM condition should be    ${vm}    RestartRequired    True

Swap VM Network On Non-Migratable VM Is Applied On Restart
    [Tags]    p1
    [Documentation]    A VM whose boot disk is ReadWriteOnce is not
    ...    live-migratable. Changing only its NAD must not ask for a restart
    ...    either: KubeVirt syncs the NAD into the VMI and sets
    ...    MigrationRequired (AutoMigrationDueToLiveUpdate), but no migration
    ...    runs and the running pod stays on the old network. The new network
    ...    is used after the next restart.
    ${vm}=    Set Variable    nsw-rwo-${SUFFIX}
    ${mac}=    Generate MAC Address
    Given VM is created with bridge NIC    ${vm}    ${IMAGE_ID}    ${SOURCE_NETWORK}    ${mac}
    ...    boot_disk_access_mode=ReadWriteOnce    &{VM_CONFIG}
    And VM should be running    ${vm}
    And VM condition reason should be    ${vm}    LiveMigratable    False    DisksNotLiveMigratable
    ${known}=    Get VM migrations    ${vm}

    When VM network is changed    ${vm}    ${NIC}    ${TARGET_NETWORK}

    Then VM condition reason should be    ${vm}    MigrationRequired    True
    ...    AutoMigrationDueToLiveUpdate    from_vmi=${True}
    And VMI network should be    ${vm}    ${NIC}    ${TARGET_NETWORK}
    And VM should not be migrated    ${vm}    ${known}
    And VM should not have condition    ${vm}    RestartRequired
    And VM launcher pod should be attached to network    ${vm}    ${SOURCE_NETWORK}    ${mac}

    When VM is restarted    ${vm}
    Then VM should be running    ${vm}
    And VM launcher pod should be attached to network    ${vm}    ${TARGET_NETWORK}    ${mac}
    And VMI interface MAC should be    ${vm}    ${NIC}    ${mac}

Reject VM Network Swap To Cluster Network With Duplicate MAC
    [Tags]    p1    negative    requires-11770
    [Documentation]    MAC addresses must be unique per cluster network. A
    ...    NAD-only change can move a NIC to another cluster network, so the
    ...    VM webhook must run its duplicate MAC check on it too
    ...    (harvester/harvester#11770): moving a NIC onto a cluster network
    ...    where another VM already uses the same MAC is rejected.
    ...    Needs a Harvester build that includes harvester/harvester#11770;
    ...    on builds without it the update is accepted and this case fails.
    ...    Both VMs stay stopped, so no migration is involved; the webhook
    ...    check does not depend on the run state.
    ${other_network}=    Set Variable    ${DEFAULT_NAMESPACE}/${DUP_CN}-vlan
    ${mac}=    Generate MAC Address
    ${owner}=    Set Variable    nsw-own-${SUFFIX}
    ${vm}=    Set Variable    nsw-dup-${SUFFIX}
    Given Create Cluster Network    ${DUP_CN}
    And Create VLAN Network    ${DUP_CN}-vlan    ${VLAN_ID}    ${DUP_CN}
    And VM is created with bridge NIC    ${owner}    ${IMAGE_ID}    ${other_network}    ${mac}
    ...    run_strategy=Halted    &{VM_CONFIG}
    And VM is created with bridge NIC    ${vm}    ${IMAGE_ID}    ${SOURCE_NETWORK}    ${mac}
    ...    run_strategy=Halted    &{VM_CONFIG}

    ${result}=    When Try To Change VM Network    ${vm}    ${NIC}    ${other_network}

    Then VM Update Should Be Rejected    ${result}    duplicate mac address


*** Keywords ***
Local Suite Setup
    Set up test environment
    ${supported}=    Cluster Version Is At Least    1.10.0
    Skip If    not ${supported}    LiveUpdateNADRef needs Harvester v1.10.0 (KubeVirt v1.9)
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${SUFFIX}    ${suffix}
    # cluster network names are at most 12 characters: nsw-<MMDDhhmm>
    ${cn}=    Generate Unique Name    nsw    precise=${FALSE}
    Set Suite Variable    ${DUP_CN}    ${cn}
    IF    '${IMAGE_ID}' == '${EMPTY}'
        Set Suite Variable    ${SUITE_IMAGE}    nsw-img-${suffix}
        Set Suite Variable    ${IMAGE_ID}    ${SUITE_IMAGE}
        Image is available for VM creation    ${SUITE_IMAGE}    ${UBUNTU_IMAGE_URL}
    END
    IF    '${SOURCE_NETWORK}' == '${EMPTY}'
        Append To List    ${SUITE_NADS}    nsw-a-${suffix}
        Create VLAN Network    nsw-a-${suffix}    ${VLAN_ID}    ${CLUSTER_NETWORK}
        Set Suite Variable    ${SOURCE_NETWORK}    ${DEFAULT_NAMESPACE}/nsw-a-${suffix}
    END
    IF    '${TARGET_NETWORK}' == '${EMPTY}'
        ${vlan_id}=    Evaluate    int($VLAN_ID) + 1
        Append To List    ${SUITE_NADS}    nsw-b-${suffix}
        Create VLAN Network    nsw-b-${suffix}    ${vlan_id}    ${CLUSTER_NETWORK}
        Set Suite Variable    ${TARGET_NETWORK}    ${DEFAULT_NAMESPACE}/nsw-b-${suffix}
    END
    IF    '${OVERLAY_NETWORK}' == '${EMPTY}'
        ${overlays}=    List VM Networks    OverlayNetwork
        IF    ${overlays}
            Set Suite Variable    ${OVERLAY_NETWORK}    ${overlays}[0]
        END
    END

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    FOR    ${nad}    IN    @{SUITE_NADS}
        Run Keyword And Ignore Error    Delete VLAN Network    ${nad}
    END
    IF    '${SUITE_IMAGE}' != '${EMPTY}'
        Run Keyword And Ignore Error    Delete image by name    ${SUITE_IMAGE}
    END
    Run Keyword If Any Tests Failed    Log Variables

Local Test Teardown
    # Test VMs are always removed with their volumes, so a failed case does
    # not leave a VM on a shared VLAN behind. Deleting a missing VM is a no-op.
    Common Test Teardown
    FOR    ${case}    IN    live    o2o    ovl    rwo    own    dup
        Run Keyword And Ignore Error    VM is deleted    nsw-${case}-${SUFFIX}
    END
    Run Keyword And Ignore Error    Delete VLAN Network    ${DUP_CN}-vlan
    # the cluster network can only go once its NAD is gone
    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    60s    5s
    ...    Delete Cluster Network    ${DUP_CN}
