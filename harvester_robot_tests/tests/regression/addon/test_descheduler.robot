*** Settings ***
Documentation    Descheduler Addon Test Cases
...              Covers the `descheduler` addon introduced by
...              https://github.com/harvester/harvester/blob/master/enhancements/20250910-descheduler.md
...              (displayName: virtual-machine-auto-balance).
...
...              This suite validates the addon contract: that Harvester ships the
...              descheduler CR with the DefaultEvictor and LowNodeUtilization
...              strategies scoped by the enhancement, that enabling it deploys the
...              chart into kube-system, and that disabling it tears the chart down.
...
...              Skip / pass-early conditions:
...                - Addon CR absent (pre-descheduler Harvester) -> whole suite skipped
...                - Cluster has < 2 nodes -> deploy/disable tests pass early, since
...                  Harvester's addon webhook rejects enabling the descheduler on
...                  single-node clusters
...
...              Not covered here:
...                - Excluded-namespace reconfiguration
...                - The upgrade re-enable flow driven by the
...                  harvesterhci.io/reenable-descheduler-addon annotation
Test Tags        regression    addons    descheduler

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/image.resource
Resource         ../../../keywords/volume.resource
Resource         ../../../keywords/virtualmachine.resource
Resource         ../../../keywords/host.resource
Resource         ../../../keywords/descheduler.resource

Suite Setup      Descheduler Suite Setup
Suite Teardown   Descheduler Suite Teardown
Test Teardown    Common Test Teardown


*** Variables ***
# Utilization thresholds used by the reconfiguration test. Deliberately different
# from the shipped 30/50 so a re-render is observable.
${TEST_THRESHOLD}           20
${TEST_TARGET_THRESHOLD}    40
# Rebalance e2e. Thresholds are derived at runtime from the measured node
# utilization rather than hardcoded, because what counts as "overutilized"
# depends entirely on how loaded the cluster already is.
${E2E_INTERVAL}             1m
# Memory request of the overload VM, as a fraction of the busy node's allocatable.
# This is roughly how many percentage points the node's utilization will jump.
${OVERLOAD_MEMORY_FRACTION}     0.30
# Never request more than this fraction of a node's free memory, so the VM both
# schedules on the busy node and still fits on the destination (nodeFit).
${NODE_FIT_FRACTION}            0.60
${MIN_OVERLOAD_MEMORY_GI}       2
# Percentage points the busy node must clear the destination by, so a threshold
# and a target threshold can be placed between them with margin either side.
${MIN_UTILIZATION_GAP}          10
${THRESHOLD_MARGIN}             10
# Two descheduling intervals plus slack: long enough that a still-active
# descheduler would have evicted something.
${E2E_SETTLE_TIME}          150s
# Grace for a live migration that was already running when the addon was disabled
${E2E_MIGRATION_SETTLE}     60s
# Set by Harvester on VMs whose VMI is not live-migratable
${PREFER_NO_EVICTION_ANNOTATION}    descheduler.alpha.kubernetes.io/prefer-no-eviction
# Populated at runtime by the suite setup
${TEST_IMAGE_NAME}          ${EMPTY}
${TEST_IMAGE_READY}         ${False}
${MIGRATABLE_VM}            ${EMPTY}
${NON_MIGRATABLE_VM}        ${EMPTY}
${RWO_VOLUME}               ${EMPTY}
${OVERLOAD_VM}              ${EMPTY}
${CORDONED_NODES}           ${EMPTY}


*** Test Cases ***
Test Descheduler Addon Ships With Expected Defaults
    [Tags]    p0    coretest
    [Documentation]    Verify the shipped descheduler addon CR matches the enhancement.
    ...               Read-only, so it runs on single-node clusters too.
    ...               Steps:
    ...                   1. Verify the addon references the descheduler chart and
    ...                      carries the virtual-machine-auto-balance labels
    ...                   2. Verify the default policy enables DefaultEvictor and
    ...                      LowNodeUtilization with utilization thresholds
    ...                   3. Verify Harvester's own namespaces are excluded from eviction
    ...               Expected Result:
    ...                   - Addon chart is `descheduler`, labelled experimental with
    ...                     displayName virtual-machine-auto-balance
    ...                   - DefaultEvictor targets virt-launcher pods with nodeFit enabled
    ...                     so VM pods can be evicted only when they fit elsewhere
    ...                   - LowNodeUtilization declares thresholds and targetThresholds
    ...                     and is the enabled balance plugin
    ...                   - harvester-system, longhorn-system and kube-system are excluded

    # Step 1: Addon identity and labels
    Then Descheduler Addon Metadata Should Be Correct

    # Step 2: Supported strategies and their configuration
    And Descheduler Default Policy Should Be Present

    # Step 3: Harvester's own workloads are never evicted
    And Descheduler Excluded Namespaces Should Contain
    ...    harvester-system    longhorn-system    kube-system

Test Descheduler Addon Deploys When Enabled
    [Tags]    p0    coretest
    [Documentation]    Verify enabling the addon deploys the descheduler into kube-system.
    ...               Steps:
    ...                   1. Pass early unless the cluster has at least 2 nodes
    ...                   2. Enable the descheduler addon and wait for the chart
    ...                   3. Wait for the descheduler pods to be Running and ready
    ...                   4. Wait for the descheduler Deployment to report ready replicas
    ...                   5. Verify the rendered policy ConfigMap carries both strategies
    ...               Expected Result:
    ...                   - Addon reaches the Completed condition
    ...                   - Deployment kube-system/descheduler is ready and its pods Running
    ...                   - ConfigMap kube-system/descheduler renders policy.yaml with
    ...                     DefaultEvictor and LowNodeUtilization
    ...               Addon state is restored by the suite teardown.

    # Step 1: Multi-node precondition enforced by Harvester's addon webhook
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2

    # Step 2: Enable the addon
    Given Descheduler Addon Is Enabled

    # Steps 3-4: Workload is deployed
    Then Descheduler Pods Should Be Running
    And Descheduler Deployment Should Be Ready

    # Step 5: The chart rendered the policy the addon declares
    And Rendered Descheduler Policy Should Contain
    ...    DeschedulerPolicy    DefaultEvictor    LowNodeUtilization

Test Descheduler Addon Is Torn Down When Disabled
    [Tags]    p0    coretest
    [Documentation]    Verify disabling the addon removes the descheduler workload, so
    ...               no further evictions can happen.
    ...               Steps:
    ...                   1. Pass early unless the cluster has at least 2 nodes
    ...                   2. Ensure the addon is enabled and deployed
    ...                   3. Disable the descheduler addon
    ...                   4. Verify the addon reports disabled
    ...                   5. Verify the Deployment, pods and policy ConfigMap are removed
    ...               Expected Result:
    ...                   - Addon spec.enabled is false
    ...                   - No pods matching app.kubernetes.io/name=descheduler remain
    ...                   - Deployment and ConfigMap kube-system/descheduler are gone

    # Step 1: Multi-node precondition enforced by Harvester's addon webhook
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2

    # Step 2: Start from a deployed descheduler
    Given Descheduler Addon Is Enabled
    And Descheduler Deployment Should Be Ready

    # Step 3: Disable
    When Descheduler Addon Is Disabled

    # Steps 4-5: Everything is torn down
    Then Descheduler Addon Should Be Disabled
    And Descheduler Deployment Should Be Gone
    And Descheduler Pods Should Be Gone
    And Descheduler Policy ConfigMap Should Be Gone

Test Descheduler Addon Cannot Be Enabled On Single Node Cluster
    [Tags]    p1    negative
    [Documentation]    Verify the addon webhook refuses to enable the descheduler when
    ...               there is nowhere to reschedule evicted VMs to.
    ...               Only runs on single-node clusters; passes early otherwise.
    ...               Steps:
    ...                   1. Pass early unless the cluster has exactly one node
    ...                   2. Attempt to enable the descheduler addon and
    ...                      verify the request was rejected with a client error
    ...                   3. Verify the addon is still disabled
    ...               Expected Result:
    ...                   - Request rejected (4xx) with "not enough nodes exist in the cluster"
    ...                   - Addon spec.enabled remains false

    # Step 1: Only meaningful on a single-node cluster
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} > 1

    # Step 2: Attempt to enable and webhook rejection
    Run Keyword and Expect Error    not enough nodes exist in the cluster    Enable    Descheduler Addon

    # Step 3: Nothing changed
    And Descheduler Addon Should Be Disabled

Test Descheduler Node Utilization Thresholds Are Configurable
    [Tags]    p1
    [Documentation]    Verify the node utilization thresholds the enhancement exposes can
    ...               be changed and reach the running descheduler.
    ...               Steps:
    ...                   1. Pass early unless the cluster has at least 2 nodes
    ...                   2. Enable the descheduler addon
    ...                   3. Set LowNodeUtilization thresholds to 20 and targets to 40
    ...                   4. Verify the addon spec carries the new thresholds
    ...                   5. Verify the chart re-rendered policy.yaml with them
    ...               Expected Result:
    ...                   - Addon spec.valuesContent reports thresholds 20/20 and
    ...                     targetThresholds 40/40
    ...                   - ConfigMap kube-system/descheduler renders the new values,
    ...                     proving the running descheduler picked up the change
    ...               Original valuesContent is restored by the suite teardown.

    # Step 1: Multi-node precondition enforced by Harvester's addon webhook
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2

    # Step 2: A running descheduler to reconfigure
    Given Descheduler Addon Is Enabled
    And Descheduler Deployment Should Be Ready

    # Step 3: Lower the thresholds
    When Descheduler Thresholds Are Set    ${TEST_THRESHOLD}    ${TEST_THRESHOLD}
    ...    ${TEST_TARGET_THRESHOLD}    ${TEST_TARGET_THRESHOLD}

    # Step 4: Persisted on the addon
    Then Descheduler Thresholds Should Be    ${TEST_THRESHOLD}    ${TEST_THRESHOLD}
    ...    ${TEST_TARGET_THRESHOLD}    ${TEST_TARGET_THRESHOLD}

    # Step 5: Reached the deployed descheduler
    And Rendered Descheduler Policy Should Contain
    ...    cpu: ${TEST_THRESHOLD}    cpu: ${TEST_TARGET_THRESHOLD}

Test Non-Migratable VM Is Excluded From Descheduling
    [Tags]    p1    virtualmachines
    [Documentation]    Verify Harvester marks non-migratable VMs so the descheduler never
    ...               evicts them, and leaves migratable VMs evictable. This controller
    ...               runs regardless of the addon state, so the test needs no addon and
    ...               works on single-node clusters.
    ...               Steps:
    ...                   1. Create a VM on the default RWX storage
    ...                   2. Verify it reports LiveMigratable and carries no
    ...                      prefer-no-eviction annotation
    ...                   3. Create a ReadWriteOnce volume
    ...                   4. Create a VM attaching that volume
    ...                   5. Verify it reports LiveMigratable=False and is annotated
    ...                      descheduler.alpha.kubernetes.io/prefer-no-eviction=true
    ...               Expected Result:
    ...                   - Migratable VM: no annotation, so the descheduler may evict it
    ...                   - Non-migratable VM: annotated, so the descheduler skips it

    Given Test Image Is Available

    # Steps 1-2: A migratable VM stays evictable
    When VM is created    ${MIGRATABLE_VM}    ${TEST_IMAGE_NAME}
    And VM should be running    ${MIGRATABLE_VM}
    Then VM condition should be    ${MIGRATABLE_VM}    LiveMigratable    True
    And VM annotation should be absent    ${MIGRATABLE_VM}    ${PREFER_NO_EVICTION_ANNOTATION}

    # Steps 3-5: An RWO volume makes the VM non-migratable, so it must be excluded
    When Create Volume    ${RWO_VOLUME}    ${DEFAULT_VOLUME_SIZE}    access_mode=ReadWriteOnce
    And Wait Until Volume Is Active    ${RWO_VOLUME}
    And VM is created with existing volume    ${NON_MIGRATABLE_VM}    ${TEST_IMAGE_NAME}
    ...    ${RWO_VOLUME}
    And VM should be running    ${NON_MIGRATABLE_VM}
    Then VM condition should be    ${NON_MIGRATABLE_VM}    LiveMigratable    False
    And VM annotation should be    ${NON_MIGRATABLE_VM}    ${PREFER_NO_EVICTION_ANNOTATION}    true

    [Teardown]    Delete Annotation Test Resources

Test VM Is Rebalanced Off An Overutilized Node
    [Tags]    p1
    [Documentation]    The enhancement's own test plan, driven by the cluster's real
    ...               utilization: make one node overutilized with a single large VM,
    ...               derive thresholds that straddle it and an idle node, and confirm
    ...               the VM is live-migrated away. Then confirm a disabled descheduler
    ...               evicts nothing.
    ...
    ...               LowNodeUtilization is *requests*-based (Harvester does not enable
    ...               metricsUtilization), so the VM's memory request is what moves the
    ...               node's utilization, and both the VM size and the thresholds are
    ...               computed from measurements rather than hardcoded. That keeps the
    ...               test valid on an idle lab cluster and on a busy one.
    ...
    ...               Steps:
    ...                   1. Pass early unless the cluster has at least 2 nodes
    ...                   2. Measure every standard node; pick the busiest to overload
    ...                      and the idlest as the drain destination
    ...                   3. Size a VM whose memory request lifts the busy node well
    ...                      above the destination but still fits on the destination
    ...                   4. Cordon the other nodes, create the VM, then uncordon
    ...                   5. Re-measure and set thresholds between the two nodes
    ...                   6. Enable the descheduler with a 1m descheduling interval
    ...                   7. Wait for the VM to leave the busy node
    ...                   8. Verify it is still Running (live migrated, not killed)
    ...                   9. Disable the descheduler and verify the VM then stays put
    ...               Expected Result:
    ...                   - The VM is evicted from the overutilized node and rescheduled
    ...                     onto another one
    ...                   - The VM is never destroyed
    ...                   - No further movement once the descheduler is disabled

    # Step 1: Multi-node precondition enforced by Harvester's addon webhook
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2

    Given Test Image Is Available

    # Step 2: Measure the cluster as the descheduler sees it
    ${busy}    ${destination}=    Descheduler Rebalance Nodes Are Selected
    ${busy_node}=    Set Variable    ${busy}[name]
    ${destination_node}=    Set Variable    ${destination}[name]

    # Step 3: Size the overload VM from those measurements
    ${vm_memory}=    Overload VM Memory Is Calculated    ${busy}    ${destination}

    # Step 4: Pin the VM to the busy node, then reopen the cluster
    When Overload VM Is Created On Node    ${busy_node}    ${vm_memory}
    Then VM should be running on node    ${OVERLOAD_VM}    ${busy_node}
    And Cordoned Nodes Are Restored

    # Steps 5-6: Straddle the two nodes with thresholds and start descheduling
    When Descheduler Thresholds Are Derived From Nodes    ${busy_node}    ${destination_node}
    ...    interval=${E2E_INTERVAL}
    And Descheduler Addon Is Enabled
    And Descheduler Pods Should Be Running

    # Steps 7-8: The VM was moved, and survived the move.
    # The destination node is logged rather than asserted: on a cluster with more
    # than two nodes the scheduler may pick any underutilized node, and once the VM
    # lands the roles can invert and the descheduler may move it on again.
    ${new_node}=    VM should be moved off node    ${OVERLOAD_VM}    ${busy_node}
    Log    ${OVERLOAD_VM} rebalanced ${busy_node} -> ${new_node} (expected ${destination_node})
    Then VM should be running    ${OVERLOAD_VM}
    And Should Not Be Equal    ${new_node}    ${busy_node}
    ...    msg=VM should no longer be on the overutilized node

    # Step 9: A disabled descheduler must not evict anything
    When Descheduler Addon Is Disabled
    And Descheduler Pods Should Be Gone
    # Let any migration that was already in flight finish before sampling, so the
    # baseline is a settled placement rather than a mid-migration one.
    Sleep    ${E2E_MIGRATION_SETTLE}    reason=Allow an in-flight live migration to finish
    ${settled_node}=    Get VM node    ${OVERLOAD_VM}
    Sleep    ${E2E_SETTLE_TIME}    reason=Two descheduling intervals with the addon off
    Then VM should be running on node    ${OVERLOAD_VM}    ${settled_node}
    And VM should be running    ${OVERLOAD_VM}

    [Teardown]    Delete E2E Test Resources


*** Keywords ***
Descheduler Suite Setup
    [Documentation]    Initialise the environment, skip when the addon is not shipped,
    ...    record the addon's original state for teardown, and name this suite's
    ...    resources uniquely so parallel runs cannot collide.
    Log    Setting up test environment for descheduler addon tests
    Set up test environment

    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${TEST_IMAGE_NAME}    img-desched-${suffix}
    Set Suite Variable    ${MIGRATABLE_VM}    vm-desched-mig-${suffix}
    Set Suite Variable    ${NON_MIGRATABLE_VM}    vm-desched-nomig-${suffix}
    Set Suite Variable    ${RWO_VOLUME}    vol-desched-rwo-${suffix}
    Set Suite Variable    ${OVERLOAD_VM}    vm-desched-load-${suffix}
    ${no_nodes}=    Create List
    Set Suite Variable    ${CORDONED_NODES}    ${no_nodes}

    Descheduler Addon Should Be Available
    Initial Descheduler State Is Captured
    Log    Test environment ready

Descheduler Suite Teardown
    [Documentation]    Restore the descheduler addon and the cluster's scheduling state.
    ...    No `Cleanup test resources` here: it sweeps by label across the whole cluster
    ...    and is not parallel-safe under pabot, so this suite deletes only what it named.
    Log    Running suite teardown for descheduler addon tests
    Run Keyword And Ignore Error    Cordoned Nodes Are Restored
    Descheduler State Is Restored
    Run Keyword And Ignore Error    Delete Suite Image
    Log    Suite teardown completed

Test Image Is Available
    [Documentation]    Create this suite's VM image on first use. Lazy so runs that only
    ...    exercise the addon (the p0 cases) never pay for an image download.
    IF    ${TEST_IMAGE_READY}
        Log    Image ${TEST_IMAGE_NAME} is already available
        RETURN
    END
    Image is available for VM creation    ${TEST_IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    Set Suite Variable    ${TEST_IMAGE_READY}    ${True}

Delete Suite Image
    [Documentation]    Remove the image created by `Test Image Is Available`, if any
    IF    ${TEST_IMAGE_READY}
        Delete image by name    ${TEST_IMAGE_NAME}
    END

Delete Annotation Test Resources
    [Documentation]    Teardown for the prefer-no-eviction test. The VM must go before
    ...    the volume it attaches, otherwise the PVC deletion blocks.
    Common Test Teardown
    Run Keyword And Ignore Error    VM is deleted    ${NON_MIGRATABLE_VM}
    Run Keyword And Ignore Error    VM is deleted    ${MIGRATABLE_VM}
    Run Keyword And Ignore Error    Delete Volume    ${RWO_VOLUME}

Only Node Is Schedulable
    [Arguments]    ${keep_node}
    [Documentation]    Cordon every standard node except ${keep_node}, so the next VM can
    ...    only land there. Records what was cordoned for later restoration.
    ${nodes}=    List Standard Nodes
    ${cordoned}=    Create List
    FOR    ${node}    IN    @{nodes}
        IF    '${node}' != '${keep_node}'
            Cordon node named    ${node}
            Append To List    ${cordoned}    ${node}
        END
    END
    Set Suite Variable    ${CORDONED_NODES}    ${cordoned}
    Log    Cordoned ${cordoned}; only ${keep_node} is schedulable

Cordoned Nodes Are Restored
    [Documentation]    Uncordon everything `Only Node Is Schedulable` cordoned.
    ...    Safe to call more than once; the record is cleared each time.
    FOR    ${node}    IN    @{CORDONED_NODES}
        Run Keyword And Ignore Error    Uncordon node named    ${node}
    END
    ${no_nodes}=    Create List
    Set Suite Variable    ${CORDONED_NODES}    ${no_nodes}

Overload VM Is Created On Node
    [Arguments]    ${node_name}    ${memory}
    [Documentation]    Create the overload VM pinned to ${node_name} by cordoning every
    ...    other node first.
    ...
    ...    requests_memory is passed explicitly because the framework otherwise hardcodes
    ...    a 2730Mi request regardless of guest size, and it is the *request* that
    ...    LowNodeUtilization measures.
    Only Node Is Schedulable    ${node_name}
    VM is created    ${OVERLOAD_VM}    ${TEST_IMAGE_NAME}    ${DEFAULT_VM_CPU}    ${memory}
    ...    requests_memory=${memory}
    VM should be running    ${OVERLOAD_VM}

Delete E2E Test Resources
    [Documentation]    Teardown for the rebalance e2e. Uncordons first so the cluster is
    ...    left schedulable even when the test failed midway.
    Common Test Teardown
    Run Keyword And Ignore Error    Cordoned Nodes Are Restored
    Run Keyword And Ignore Error    VM is deleted    ${OVERLOAD_VM}
