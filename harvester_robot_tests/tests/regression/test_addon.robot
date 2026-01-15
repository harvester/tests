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
${PROMETHEUS_POD_PREFIX}     prometheus-rancher-monitoring
${LOCAL_PROMETHEUS_PORT}     9090

*** Test Cases ***
Test Rancher-Monitoring Addon Enable Disable And Functionality
    [Tags]    p0    coretest
    [Documentation]    Test complete lifecycle of rancher-monitoring addon
    ...               Steps:
    ...               1. Store the initial state of the monitoring addon
    ...               2. Enable the rancher-monitoring addon and wait for it to deploy
    ...               3. Verify that key monitoring pods (Prometheus, Grafana) are running
    ...               4. Port-forward to the Prometheus pod
    ...               5. Query Prometheus for essential Harvester metrics
    ...               6. Verify that all metric queries are successful
    ...               7. Restore the addon to its initial state (teardown)
    ...               Expected Result:
    ...               - Addon can be enabled and disabled successfully
    ...               - Monitoring pods deploy and become ready
    ...               - Prometheus is accessible and returns Harvester metrics
    ...               - Addon state is restored after test

    # Step 1: Store initial state
    Log    Step 1: Getting initial state of addon
    ${initial_state}=    Get Addon Initial State    ${ADDON_NAME}
    Log    Initial addon state: ${initial_state}
    Set Suite Variable    ${INITIAL_ADDON_STATE}    ${initial_state}

    # Step 2: Enable addon if not already enabled
    Log    Step 2: Enabling rancher-monitoring addon
    ${is_enabled}=    Is Addon Enabled    ${ADDON_NAME}
    Run Keyword If    not ${is_enabled}    Enable Addon    ${ADDON_NAME}
    Wait For Addon Enabled    ${ADDON_NAME}    timeout=900

    # Step 3: Verify monitoring pods are running
    Log    Step 3: Verifying monitoring pods are running
    Wait For Monitoring Pods Running    ${MONITORING_NAMESPACE}    timeout=900

    # Step 4: Get Prometheus pod name and setup port-forward
    Log    Step 4: Setting up port-forward to Prometheus
    ${prometheus_pod}=    Get Prometheus Pod Name
    Port Forward To Prometheus    ${MONITORING_NAMESPACE}    ${prometheus_pod}    ${LOCAL_PROMETHEUS_PORT}
    Sleep    5s    Wait for port-forward to stabilize

    # Step 5 & 6: Query Prometheus for essential metrics
    Log    Step 5-6: Querying Prometheus for Harvester metrics
    Verify Essential Harvester Metrics

    # Cleanup port-forward
    Stop Port Forward

    Log    Test completed successfully

*** Keywords ***
Suite Setup For Addon Tests
    [Documentation]    Initialize test environment for addon tests
    Log    Setting up test environment for addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For Addon Tests
    [Documentation]    Cleanup and restore addon state after tests
    Log    Running suite teardown for addon tests
    
    # Stop port forward if still running
    Run Keyword And Ignore Error    Stop Port Forward
    
    # Restore addon to initial state
    Run Keyword If    '${INITIAL_ADDON_STATE}' != '${NONE}'
    ...    Restore Addon State    ${ADDON_NAME}    ${INITIAL_ADDON_STATE}
    
    # Standard cleanup
    Cleanup test resources
    Log    Suite teardown completed

Get Prometheus Pod Name
    [Documentation]    Get the name of the Prometheus pod
    Log    Getting Prometheus pod name
    
    # Use kubectl to get pod name
    ${result}=    Run Process    kubectl    get    pods
    ...    -n    ${MONITORING_NAMESPACE}
    ...    -l    app.kubernetes.io/name=prometheus
    ...    -o    jsonpath={.items[0].metadata.name}
    ...    shell=False
    
    Should Be Equal As Numbers    ${result.rc}    0    Failed to get Prometheus pod name
    ${pod_name}=    Set Variable    ${result.stdout}
    Should Not Be Empty    ${pod_name}    Prometheus pod name should not be empty
    
    Log    Found Prometheus pod: ${pod_name}
    [Return]    ${pod_name}

Verify Essential Harvester Metrics
    [Documentation]    Verify that essential Harvester metrics are available in Prometheus
    Log    Verifying essential Harvester metrics
    
    # Define essential Harvester metrics to verify
    @{metrics}=    Create List
    ...    up
    ...    node_cpu_seconds_total
    ...    node_memory_MemTotal_bytes
    ...    kubevirt_vmi_info
    ...    kubevirt_vm_container_cpu_usage_seconds_total
    
    # Query and verify each metric
    FOR    ${metric}    IN    @{metrics}
        Log    Verifying metric: ${metric}
        Verify Prometheus Metric Exists    ${metric}
    END
    
    Log    All essential metrics verified successfully
