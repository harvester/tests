*** Settings ***
Documentation    Descheduler Addon Keywords - Reusable keywords for the
...              `descheduler` addon (displayName: virtual-machine-auto-balance).
...
...              The addon CR lives in kube-system and ships disabled. Enabling it
...              renders the upstream kubernetes-sigs/descheduler chart, which
...              creates a Deployment and a ConfigMap both named `descheduler`
...              (the helm release name equals the chart name, so
...              `descheduler.fullname` collapses to `descheduler`).
Library          Collections
Resource         variables.resource
Resource         common.resource
Resource         pod.resource
Resource         addon.resource
Resource         deployment.resource
Resource         host.resource
Resource         virtualmachine.resource

*** Variables ***
${ADDON_DESCHEDULER}            descheduler
${DESCHEDULER_NAMESPACE}        kube-system
${DESCHEDULER_LABEL}            app.kubernetes.io/name=descheduler
${DESCHEDULER_DEPLOYMENT}       descheduler
${DESCHEDULER_CONFIGMAP}        descheduler
${DESCHEDULER_POLICY_KEY}       policy.yaml
${DESCHEDULER_DISPLAY_NAME}     virtual-machine-auto-balance
# Populated at runtime by `Initial Descheduler State Is Captured`; declared here
# so teardown is safe even when the suite skipped before capturing anything.
${INITIAL_STATE_DESCHEDULER}    ${None}
${INITIAL_VALUES_DESCHEDULER}   ${None}

*** Keywords ***
Descheduler Addon Should Be Available
    [Documentation]    Skip the suite when the descheduler addon CR is absent.
    ...    The addon only exists on Harvester releases that shipped the
    ...    descheduler enhancement, so older clusters skip instead of failing.
    ${exists}=    addon.Addon Exists    ${ADDON_DESCHEDULER}
    IF    not ${exists}
        Skip    descheduler addon CR not found - cluster predates the descheduler enhancement
    END
    Log    Descheduler addon CR is present

# Addon state
Initial Descheduler State Is Captured
    [Documentation]    Capture the addon's enabled flag and raw valuesContent so
    ...    teardown can restore the cluster exactly as it was found.
    ${initial_state}=    addon.Get Initial State    ${ADDON_DESCHEDULER}
    ${initial_values}=    addon.Get Addon Values Content    ${ADDON_DESCHEDULER}
    Set Suite Variable    ${INITIAL_STATE_DESCHEDULER}    ${initial_state}
    Set Suite Variable    ${INITIAL_VALUES_DESCHEDULER}    ${initial_values}
    Log    Captured descheduler addon state: enabled=${initial_state}

Descheduler Addon Is Enabled
    [Documentation]    Enable the descheduler addon and wait for the chart to deploy
    ${is_enabled}=    addon.Is Enabled    ${ADDON_DESCHEDULER}
    IF    not ${is_enabled}
        addon.Enable    ${ADDON_DESCHEDULER}
    END
    addon.Wait For Enabled    ${ADDON_DESCHEDULER}
    Log    Descheduler addon is enabled

Descheduler Addon Is Disabled
    [Documentation]    Disable the descheduler addon and wait for the spec to settle
    ${is_enabled}=    addon.Is Enabled    ${ADDON_DESCHEDULER}
    IF    ${is_enabled}
        addon.Disable    ${ADDON_DESCHEDULER}
    END
    addon.Wait For Disabled    ${ADDON_DESCHEDULER}
    Log    Descheduler addon is disabled

Descheduler Addon Should Be Disabled
    [Documentation]    Assert the addon's spec.enabled is currently false
    ${is_enabled}=    addon.Is Enabled    ${ADDON_DESCHEDULER}
    Should Not Be True    ${is_enabled}    msg=Descheduler addon should be disabled

Descheduler State Is Restored
    [Documentation]    Restore the addon's valuesContent and enabled flag captured by
    ...    `Initial Descheduler State Is Captured`. Values are restored first so the
    ...    addon is never re-enabled with a test's modified configuration.
    IF    $INITIAL_VALUES_DESCHEDULER is not None
        Run Keyword And Ignore Error
        ...    addon.Set Addon Values Content    ${ADDON_DESCHEDULER}
        ...    ${INITIAL_VALUES_DESCHEDULER}
    END
    IF    $INITIAL_STATE_DESCHEDULER is not None
        Run Keyword And Ignore Error
        ...    addon.Restore State    ${ADDON_DESCHEDULER}    ${INITIAL_STATE_DESCHEDULER}
    END
    Log    Descheduler addon state restored

# Addon metadata
Descheduler Addon Metadata Should Be Correct
    [Documentation]    Assert the shipped addon CR still declares the descheduler chart
    ...    and carries the labels the Harvester UI keys off.
    ${spec}=    addon.Get Addon Spec    ${ADDON_DESCHEDULER}
    Should Be Equal    ${spec}[chart]    descheduler
    ...    msg=Descheduler addon should reference the 'descheduler' chart
    ${labels}=    addon.Get Addon Labels    ${ADDON_DESCHEDULER}
    Dictionary Should Contain Item    ${labels}    addon.harvesterhci.io/displayName
    ...    ${DESCHEDULER_DISPLAY_NAME}
    Dictionary Should Contain Item    ${labels}    addon.harvesterhci.io/experimental    true
    Log    Descheduler addon metadata verified

# Policy inspection
Get Descheduler Profile
    [Documentation]    Return the first profile of the addon's deschedulerPolicy.
    ...    Harvester ships exactly one profile named `default`.
    ...    Returns:
    ...        dict: The profile, containing `pluginConfig` and `plugins`
    ${values}=    addon.Get Addon Values    ${ADDON_DESCHEDULER}
    Dictionary Should Contain Key    ${values}    deschedulerPolicy
    ...    msg=Descheduler addon valuesContent should define deschedulerPolicy
    ${policy}=    Set Variable    ${values}[deschedulerPolicy]
    Dictionary Should Contain Key    ${policy}    profiles
    ...    msg=deschedulerPolicy should define profiles
    ${profiles}=    Set Variable    ${policy}[profiles]
    Should Not Be Empty    ${profiles}    msg=deschedulerPolicy should define at least one profile
    RETURN    ${profiles}[0]

Get Descheduler Plugin Args
    [Arguments]    ${plugin_name}
    [Documentation]    Return the `args` of a named entry in the profile's pluginConfig
    ...    Args:
    ...        plugin_name: e.g. DefaultEvictor or LowNodeUtilization
    ...    Returns:
    ...        dict: The plugin's args
    ${profile}=    Get Descheduler Profile
    Dictionary Should Contain Key    ${profile}    pluginConfig
    ...    msg=Descheduler profile should define pluginConfig
    ${plugin_configs}=    Set Variable    ${profile}[pluginConfig]
    FOR    ${entry}    IN    @{plugin_configs}
        ${name}=    Get From Dictionary    ${entry}    name    default=${EMPTY}
        IF    '${name}' == '${plugin_name}'
            Dictionary Should Contain Key    ${entry}    args
            ...    msg=Descheduler plugin ${plugin_name} declares no args
            RETURN    ${entry}[args]
        END
    END
    Fail    Descheduler pluginConfig has no entry named ${plugin_name}

Descheduler Default Policy Should Be Present
    [Documentation]    Assert the shipped policy enables the two strategies the
    ...    enhancement scopes: DefaultEvictor and LowNodeUtilization.
    ...    DefaultEvictor must target virt-launcher pods so VM pods can be evicted,
    ...    and LowNodeUtilization must be the enabled balance plugin.
    ${values}=    addon.Get Addon Values    ${ADDON_DESCHEDULER}
    Dictionary Should Contain Key    ${values}    deschedulingInterval
    ...    msg=Descheduler addon should define a deschedulingInterval

    ${evictor_args}=    Get Descheduler Plugin Args    DefaultEvictor
    Dictionary Should Contain Item    ${evictor_args}    nodeFit    ${True}
    ...    msg=DefaultEvictor should only evict pods that fit on another node
    ${selector}=    Set Variable    ${evictor_args}[labelSelector]
    ${selector_text}=    Convert To String    ${selector}
    Should Contain    ${selector_text}    virt-launcher
    ...    msg=DefaultEvictor labelSelector should target virt-launcher (VM) pods

    ${low_args}=    Get Descheduler Plugin Args    LowNodeUtilization
    Dictionary Should Contain Key    ${low_args}    thresholds
    ...    msg=LowNodeUtilization should define utilization thresholds
    Dictionary Should Contain Key    ${low_args}    targetThresholds
    ...    msg=LowNodeUtilization should define target utilization thresholds

    ${profile}=    Get Descheduler Profile
    ${balance}=    Set Variable    ${profile}[plugins][balance][enabled]
    Should Contain    ${balance}    LowNodeUtilization
    ...    msg=LowNodeUtilization should be enabled as a balance plugin
    Log    Descheduler default policy verified

Descheduler Excluded Namespaces Should Contain
    [Arguments]    @{namespaces}
    [Documentation]    Assert LowNodeUtilization never evicts from the given namespaces
    ${low_args}=    Get Descheduler Plugin Args    LowNodeUtilization
    ${excluded}=    Set Variable    ${low_args}[evictableNamespaces][exclude]
    FOR    ${namespace}    IN    @{namespaces}
        Should Contain    ${excluded}    ${namespace}
        ...    msg=${namespace} should be excluded from descheduler eviction
    END
    Log    Descheduler excluded namespaces verified

# Policy configuration
Descheduler Thresholds Are Set
    [Arguments]    ${cpu}    ${memory}    ${target_cpu}    ${target_memory}
    ...    ${interval}=${None}
    [Documentation]    Rewrite the LowNodeUtilization utilization thresholds, and
    ...    optionally the deschedulingInterval, in a single addon update.
    ...
    ...    Nodes below `thresholds` are treated as underutilized and receive pods;
    ...    nodes above `targetThresholds` are overutilized and get pods evicted.
    ...    Values are coerced to integers so they serialise as YAML numbers - the
    ...    descheduler rejects quoted strings here.
    ...    Args:
    ...        cpu, memory: underutilization thresholds (percent)
    ...        target_cpu, target_memory: overutilization thresholds (percent)
    ...        interval: optional deschedulingInterval, e.g. 1m
    ${values}=    addon.Get Addon Values    ${ADDON_DESCHEDULER}
    ${cpu}=    Convert To Integer    ${cpu}
    ${memory}=    Convert To Integer    ${memory}
    ${target_cpu}=    Convert To Integer    ${target_cpu}
    ${target_memory}=    Convert To Integer    ${target_memory}
    ${thresholds}=    Create Dictionary    cpu=${cpu}    memory=${memory}
    ${targets}=    Create Dictionary    cpu=${target_cpu}    memory=${target_memory}

    # The parsed values still share the nested dicts, so mutating an entry's args
    # here also mutates ${values} that gets written back below.
    ${plugin_configs}=    Set Variable    ${values}[deschedulerPolicy][profiles][0][pluginConfig]
    ${updated}=    Set Variable    ${False}
    FOR    ${entry}    IN    @{plugin_configs}
        ${name}=    Get From Dictionary    ${entry}    name    default=${EMPTY}
        IF    '${name}' == 'LowNodeUtilization'
            Set To Dictionary    ${entry}[args]    thresholds=${thresholds}
            Set To Dictionary    ${entry}[args]    targetThresholds=${targets}
            ${updated}=    Set Variable    ${True}
        END
    END
    Should Be True    ${updated}
    ...    msg=Descheduler pluginConfig has no LowNodeUtilization entry to configure

    IF    $interval is not None
        Set To Dictionary    ${values}    deschedulingInterval=${interval}
    END

    addon.Set Addon Values    ${ADDON_DESCHEDULER}    ${values}
    Log    Descheduler thresholds set to ${cpu}/${memory}, targets ${target_cpu}/${target_memory}

Descheduler Thresholds Should Be
    [Arguments]    ${cpu}    ${memory}    ${target_cpu}    ${target_memory}
    [Documentation]    Assert the addon spec carries the given LowNodeUtilization thresholds
    ${low_args}=    Get Descheduler Plugin Args    LowNodeUtilization
    Should Be Equal As Integers    ${low_args}[thresholds][cpu]    ${cpu}
    ...    msg=Underutilization cpu threshold should be ${cpu}
    Should Be Equal As Integers    ${low_args}[thresholds][memory]    ${memory}
    ...    msg=Underutilization memory threshold should be ${memory}
    Should Be Equal As Integers    ${low_args}[targetThresholds][cpu]    ${target_cpu}
    ...    msg=Overutilization cpu threshold should be ${target_cpu}
    Should Be Equal As Integers    ${low_args}[targetThresholds][memory]    ${target_memory}
    ...    msg=Overutilization memory threshold should be ${target_memory}
    Log    Descheduler thresholds verified in the addon spec

# Deployed workload
Descheduler Pods Should Be Running
    [Documentation]    Wait for the descheduler pods to be Running and ready
    Wait For Pods Running    ${DESCHEDULER_NAMESPACE}    ${DESCHEDULER_LABEL}

Descheduler Deployment Should Be Ready
    [Documentation]    Wait for the descheduler Deployment to report all replicas ready
    Wait For Deployment Ready    ${DESCHEDULER_DEPLOYMENT}    ${DESCHEDULER_NAMESPACE}

Descheduler Pods Should Be Gone
    [Documentation]    Wait until no descheduler pods remain
    Wait For Pods Gone    ${DESCHEDULER_NAMESPACE}    ${DESCHEDULER_LABEL}

Descheduler Deployment Should Be Gone
    [Documentation]    Wait until the descheduler Deployment has been uninstalled
    Wait For Deployment Gone    ${DESCHEDULER_DEPLOYMENT}    ${DESCHEDULER_NAMESPACE}

Get Rendered Descheduler Policy
    [Documentation]    Return the policy.yaml rendered into the descheduler ConfigMap.
    ...    Reading the rendered policy (rather than the addon spec) proves the chart
    ...    was actually deployed with the configuration under test.
    ...    Returns:
    ...        str: Contents of the policy.yaml key
    ${data}=    addon.Get ConfigMap Data    ${DESCHEDULER_CONFIGMAP}    ${DESCHEDULER_NAMESPACE}
    Should Not Be Equal    ${data}    ${None}
    ...    msg=ConfigMap ${DESCHEDULER_NAMESPACE}/${DESCHEDULER_CONFIGMAP} was not rendered
    Dictionary Should Contain Key    ${data}    ${DESCHEDULER_POLICY_KEY}
    ...    msg=Descheduler ConfigMap should contain ${DESCHEDULER_POLICY_KEY}
    RETURN    ${data}[${DESCHEDULER_POLICY_KEY}]

Rendered Descheduler Policy Should Contain
    [Arguments]    @{expected}
    [Documentation]    Poll the rendered policy.yaml until it contains every expected
    ...    fragment. Polled because the helm job re-renders the ConfigMap
    ...    asynchronously after the addon spec changes.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Rendered Descheduler Policy Contains    @{expected}

Rendered Descheduler Policy Contains
    [Arguments]    @{expected}
    [Documentation]    Single-shot assertion backing `Rendered Descheduler Policy Should Contain`
    ${policy}=    Get Rendered Descheduler Policy
    FOR    ${fragment}    IN    @{expected}
        Should Contain    ${policy}    ${fragment}
        ...    msg=Rendered descheduler policy should contain '${fragment}'
    END

Descheduler Policy ConfigMap Should Be Gone
    [Documentation]    Wait until the rendered descheduler ConfigMap is removed
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Descheduler Policy ConfigMap Is Absent

Descheduler Policy ConfigMap Is Absent
    [Documentation]    Single-shot assertion backing `Descheduler Policy ConfigMap Should Be Gone`
    ${data}=    addon.Get ConfigMap Data    ${DESCHEDULER_CONFIGMAP}    ${DESCHEDULER_NAMESPACE}
    Should Be Equal    ${data}    ${None}
    ...    msg=ConfigMap ${DESCHEDULER_NAMESPACE}/${DESCHEDULER_CONFIGMAP} still exists

# Node utilization, measured the way LowNodeUtilization measures it
Get Standard Node Utilizations
    [Documentation]    Return the requests-based utilization of every standard node,
    ...    sorted ascending by memory utilization (least loaded first).
    ${nodes}=    List Standard Nodes
    ${utilizations}=    Create List
    FOR    ${node}    IN    @{nodes}
        ${utilization}=    Get node resource utilization    ${node}
        Append To List    ${utilizations}    ${utilization}
    END
    ${sorted}=    Evaluate    sorted($utilizations, key=lambda u: u['memory_percent'])
    FOR    ${utilization}    IN    @{sorted}
        Log    ${utilization}[name]: cpu ${utilization}[cpu_percent]%, memory ${utilization}[memory_percent]%
    END
    RETURN    ${sorted}

Descheduler Rebalance Nodes Are Selected
    [Documentation]    Pick which node to overload and which node the descheduler should
    ...    drain to. The busiest node is overloaded because it needs the least extra
    ...    memory to cross the target threshold; the idlest is the drain destination
    ...    because it has the most headroom for DefaultEvictor's nodeFit check.
    ...    Returns the busy and destination utilization dicts.
    ${utilizations}=    Get Standard Node Utilizations
    ${count}=    Get Length    ${utilizations}
    Should Be True    ${count} >= 2
    ...    msg=Rebalancing needs at least 2 standard nodes, found ${count}
    ${destination}=    Set Variable    ${utilizations}[0]
    ${busy}=    Set Variable    ${utilizations}[-1]
    Log    Will overload ${busy}[name] and expect eviction towards ${destination}[name]
    RETURN    ${busy}    ${destination}

Overload VM Memory Is Calculated
    [Arguments]    ${busy}    ${destination}
    [Documentation]    Size a VM whose memory *request* pushes ${busy} clear of
    ...    ${destination}, while still fitting on ${destination} so DefaultEvictor's
    ...    nodeFit check allows the eviction.
    ...
    ...    LowNodeUtilization is requests-based, so the guest memory only matters
    ...    because the framework mirrors it into the pod request.
    ...    Passes the test early when the cluster has too little free memory to build a
    ...    meaningfully overutilized node.
    ...    Returns a Kubernetes memory quantity such as "8Gi".
    ${gib}=    Evaluate
    ...    int(min($busy['memory_allocatable'] * ${OVERLOAD_MEMORY_FRACTION}, $busy['memory_available'] * ${NODE_FIT_FRACTION}, $destination['memory_available'] * ${NODE_FIT_FRACTION}) // (1024 ** 3))
    Pass Execution If    ${gib} < ${MIN_OVERLOAD_MEMORY_GI}
    ...    Not enough free memory to overload a node (computed ${gib}Gi, need ${MIN_OVERLOAD_MEMORY_GI}Gi)

    ${projected}=    Evaluate
    ...    round(($busy['memory_requested'] + ${gib} * 1024 ** 3) / $busy['memory_allocatable'] * 100, 1)
    ${gap}=    Evaluate    round(${projected} - $destination['memory_percent'], 1)
    Pass Execution If    ${gap} < ${MIN_UTILIZATION_GAP}
    ...    Projected utilization gap of ${gap} points is too small to separate thresholds
    Log    A ${gib}Gi VM should take ${busy}[name] to ~${projected}% memory, ${gap} points above ${destination}[name]
    RETURN    ${gib}Gi

Descheduler Thresholds Are Derived From Nodes
    [Arguments]    ${busy_node}    ${destination_node}    ${interval}=${None}
    [Documentation]    Re-measure both nodes and set thresholds that straddle them, so
    ...    LowNodeUtilization classifies ${busy_node} as overutilized and
    ...    ${destination_node} as underutilized.
    ...
    ...    Memory drives the decision; targetThresholds.cpu is pinned to 100 so CPU can
    ...    never mark a node overutilized on its own. thresholds.cpu still has to sit
    ...    above the destination's CPU usage, because a node only counts as
    ...    underutilized when every resource is below its threshold.
    ${busy}=    Get node resource utilization    ${busy_node}
    ${dest}=    Get node resource utilization    ${destination_node}

    ${threshold_memory}=    Evaluate
    ...    max(1, min(100, math.ceil($dest['memory_percent']) + ${THRESHOLD_MARGIN}))    modules=math
    ${target_memory}=    Evaluate
    ...    max(1, min(100, math.floor($busy['memory_percent']) - ${THRESHOLD_MARGIN}))    modules=math
    Should Be True    ${threshold_memory} <= ${target_memory}
    ...    msg=Cannot straddle the nodes: ${destination_node} is at ${dest}[memory_percent]% and ${busy_node} at ${busy}[memory_percent]% memory
    ${threshold_cpu}=    Evaluate
    ...    max(1, min(100, math.ceil($dest['cpu_percent']) + ${THRESHOLD_MARGIN}))    modules=math

    Descheduler Thresholds Are Set    ${threshold_cpu}    ${threshold_memory}
    ...    100    ${target_memory}    interval=${interval}
    Log    ${busy_node} at ${busy}[memory_percent]% memory is above target ${target_memory}%; ${destination_node} at ${dest}[memory_percent]% is below threshold ${threshold_memory}%
