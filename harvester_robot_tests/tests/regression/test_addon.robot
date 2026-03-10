*** Settings ***
Documentation    Rancher-Monitoring Addon Test Cases
...             This suite tests the enable, disable, and basic functionality
...             of the Rancher-Monitoring add-on in Harvester.
Test Tags        regression    addons    rancher-monitoring

Library          Process
Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/addon.resource

Suite Setup      Suite Setup For Addon Tests
Suite Teardown   Suite Teardown For Addon Tests

*** Variables ***
${ADDON_MONITORING}          rancher-monitoring
${MONITORING_NAMESPACE}      cattle-monitoring-system
${LOCAL_PROMETHEUS_PORT}     9090
${ADDON_PCIDEVICES}           pcidevices-controller
${PCIDEVICES_NAMESPACE}       harvester-system
${PCIDEVICES_CONTROLLER_LABEL}    app.kubernetes.io/name=harvester-pcidevices-controller
${PCIDEVICES_WEBHOOK_SERVICE}     pcidevices-webhook
${INITIAL_STATE_MONITORING}     Initial state of monitoring addon (captured at runtime)
${INITIAL_STATE_PCIDEVICES}     ${None}

*** Test Cases ***
Test Rancher Monitoring Addon Deploys And Accessibility
    [Tags]    p0    coretest
    [Documentation]    Verify rancher-monitoring addon can be enabled and Prometheus metrics are accessible
    ...               Given: The initial addon state is captured
    ...               When: The rancher-monitoring addon is enabled
    ...               Then: Monitoring pods are running and Prometheus metrics are queryable

    # Given: Capture initial addon state for teardown restoration
    Given Initial Addon State Is Captured    ${ADDON_MONITORING}

    # When: Enable the monitoring addon
    When Monitoring Addon Is Enabled    ${ADDON_MONITORING}

    # Then: Verify deployment and metrics
    Then Monitoring Pods Should Be Running    ${MONITORING_NAMESPACE}
    And Prometheus Should Be Accessible    ${MONITORING_NAMESPACE}
    And Essential Harvester Metrics Should Exist

    # Cleanup
    [Teardown]    Addon - Stop Port Forward

Test PCI Devices Controller Addon Deploys And Accessibility
    [Tags]    p0    coretest    pcidevices-controller
    [Documentation]    Verify pcidevices-controller addon can be enabled and pods/services are accessible
    ...               Steps:
    ...                   1. Capture initial addon state
    ...                   2. Enable the addon
    ...                   3. Wait for controller pods running
    ...                   4. Verify webhook service running
    ...                   5. Restore addon state (teardown)
    ...               Expected Result:
    ...                   - Addon enabled
    ...                   - Controller pods running
    ...                   - Webhook service accessible

    # Given: Capture initial addon state for teardown restoration
    Given Initial PCI Addon State Is Captured    ${ADDON_PCIDEVICES}

    # When: Enable the pcidevices-controller addon
    When PCI Devices Addon Is Enabled    ${ADDON_PCIDEVICES}

    # Then: Verify deployment and services
    Then PCI Devices Controller Pods Should Be Running    ${PCIDEVICES_NAMESPACE}    ${PCIDEVICES_CONTROLLER_LABEL}
    And PCI Devices Webhook Service Should Be Running    ${PCIDEVICES_NAMESPACE}    ${PCIDEVICES_WEBHOOK_SERVICE}

    # Cleanup
    [Teardown]    Suite Teardown For PCI Devices Addon Tests


*** Keywords ***
# BDD Keywords
Initial Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the addon
    ${initial_state}=    Addon - Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_MONITORING}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

Monitoring Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the monitoring addon and wait for deployment
    ${is_enabled}=    Addon - Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Addon - Enable    ${addon_name}
    Addon - Wait For Enabled    ${addon_name}    timeout=900
    Log    Monitoring addon ${addon_name} is enabled

Monitoring Pods Should Be Running
    [Arguments]    ${namespace}
    [Documentation]    Verify monitoring pods are running
    Addon - Wait For Monitoring Pods Running    ${namespace}    timeout=900
    Log    All monitoring pods are running in ${namespace}

Prometheus Should Be Accessible
    [Arguments]    ${namespace}
    [Documentation]    Setup port-forward and verify Prometheus is accessible
    ${prometheus_pod}=    Get Prometheus Pod Name
    Addon - Port Forward To Prometheus    ${namespace}    ${prometheus_pod}    ${LOCAL_PROMETHEUS_PORT}
    Sleep    5s    Wait for port-forward to stabilize
    Log    Prometheus is accessible via port ${LOCAL_PROMETHEUS_PORT}

Essential Harvester Metrics Should Exist
    [Documentation]    Verify essential Harvester metrics are available in Prometheus
    @{metrics}=    Create List
    ...    up
    ...    node_cpu_seconds_total
    ...    node_memory_MemTotal_bytes
    ...    kubevirt_info
    FOR    ${metric}    IN    @{metrics}
        Addon - Verify Prometheus Metric Exists    ${metric}
    END
    Log    All essential Harvester metrics verified

# Setup/Teardown Keywords
Suite Setup For Addon Tests
    [Documentation]    Initialize test environment for addon tests
    Log    Setting up test environment for addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For Addon Tests
    [Documentation]    Cleanup and restore addon state after tests
    Log    Running suite teardown for addon tests
    
    # Stop port forward if still running
    Run Keyword And Ignore Error    Addon - Stop Port Forward
    
    # Restore addon to initial state
    Run Keyword If    '${INITIAL_STATE_MONITORING}' != 'None'
    ...    Addon - Restore State    ${ADDON_MONITORING}    ${INITIAL_STATE_MONITORING}
    
    # Standard cleanup
    Cleanup test resources
    Log    Suite teardown completed

Get Prometheus Pod Name
    [Documentation]    Get the name of the Prometheus pod
    Log    Getting Prometheus pod name
    
    # Use kubectl to get pod name
    @{args}=    Create List    get    pods    -n    ${MONITORING_NAMESPACE}    -l    app.kubernetes.io/name=prometheus    -o    jsonpath={.items[0].metadata.name}
    ${result}=    Run Process    kubectl    @{args}
    
    Should Be Equal As Numbers    ${result.rc}    0    Failed to get Prometheus pod name
    ${pod_name}=    Set Variable    ${result.stdout}
    Should Not Be Empty    ${pod_name}    Prometheus pod name should not be empty
    
    Log    Found Prometheus pod: ${pod_name}
    RETURN    ${pod_name}

Initial PCI Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the addon
    ${initial_state}=    Addon - Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_PCIDEVICES}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}


PCI Devices Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the pcidevices-controller addon and wait for deployment
    ${is_enabled}=    Addon - Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Addon - Enable    ${addon_name}
    Addon - Wait For Enabled    ${addon_name}    timeout=900
    Log    PCI Devices addon ${addon_name} is enabled

PCI Devices Controller Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify pcidevices-controller pods are running
    Addon - Wait For Pods Running    ${namespace}    ${label}    timeout=900
    Log    All pcidevices-controller pods are running in ${namespace}

PCI Devices Webhook Service Should Be Running
    [Arguments]    ${namespace}    ${service_name}
    [Documentation]    Verify pcidevices-webhook service is running
    Addon - Wait For Service Running    ${namespace}    ${service_name}    timeout=300
    Log    pcidevices-webhook service is running in ${namespace}

Suite Setup For PCI Devices Addon Tests
    [Documentation]    Initialize test environment for PCI Devices addon tests
    Log    Setting up test environment for PCI Devices addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For PCI Devices Addon Tests
    [Documentation]    Cleanup and restore addon state after tests
    Log    Running suite teardown for PCI Devices addon tests
    Run Keyword If    '${INITIAL_STATE_PCIDEVICES}' != ${None}
    ...    Addon - Restore State    ${ADDON_PCIDEVICES}    ${INITIAL_STATE_PCIDEVICES}
    Cleanup test resources
    Log    Suite teardown completed
