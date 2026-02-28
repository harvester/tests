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
${ADDON_NAME}                rancher-monitoring
${MONITORING_NAMESPACE}      cattle-monitoring-system
${LOCAL_PROMETHEUS_PORT}     9090

*** Test Cases ***
Test Rancher Monitoring Addon Deploys And Accessibility
    [Tags]    p0    coretest
    [Documentation]    Verify rancher-monitoring addon can be enabled and Prometheus metrics are accessible
    ...               Given: The initial addon state is captured
    ...               When: The rancher-monitoring addon is enabled
    ...               Then: Monitoring pods are running and Prometheus metrics are queryable

    # Given: Capture initial addon state for teardown restoration
    Given Initial Addon State Is Captured    ${ADDON_NAME}

    # When: Enable the monitoring addon
    When Monitoring Addon Is Enabled    ${ADDON_NAME}

    # Then: Verify deployment and metrics
    Then Monitoring Pods Should Be Running    ${MONITORING_NAMESPACE}
    And Prometheus Should Be Accessible    ${MONITORING_NAMESPACE}
    And Essential Harvester Metrics Should Exist

    # Cleanup
    [Teardown]    Addon - Stop Port Forward

*** Keywords ***
# BDD Keywords
Initial Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the addon
    ${initial_state}=    Addon - Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_ADDON_STATE}    ${initial_state}
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
    ...    kubevirt_vmi_info
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
    Run Keyword If    '${INITIAL_ADDON_STATE}' != 'None'
    ...    Addon - Restore State    ${ADDON_NAME}    ${INITIAL_ADDON_STATE}
    
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
