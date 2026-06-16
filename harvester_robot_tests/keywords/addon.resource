*** Settings ***
Documentation    Addon Keywords - Reusable keywords for addon operations
Library          ../libs/keywords/addon_keywords.py
Library          Process
Resource         variables.resource
Resource         common.resource

*** Variables ***
${LVM_ADDON_URL}    https://raw.githubusercontent.com/harvester/experimental-addons/main/harvester-csi-driver-lvm/harvester-csi-driver-lvm.yaml

*** Keywords ***
Install Addon From URL
    [Arguments]    ${url}
    [Documentation]    Install an addon by applying a YAML manifest from the given URL
    Log    Installing addon from ${url}
    addon_keywords.install_addon_yaml    ${url}
    Log    Addon YAML applied successfully

Get Addon Initial State
    [Arguments]    ${addon_name}
    [Documentation]    Get initial state of addon (enabled/disabled)
    ...               Args:
    ...                   addon_name: Name of the addon
    ...               Returns:
    ...                   bool: True if enabled, False if disabled
    Log    Getting initial state of addon: ${addon_name}
    ${initial_state}=    addon_keywords.get_addon_initial_state    ${addon_name}
    Log    Addon ${addon_name} initial state: ${initial_state}
    RETURN    ${initial_state}

Enable Addon
    [Arguments]    ${addon_name}
    [Documentation]    Enable an addon
    ...               Args:
    ...                   addon_name: Name of the addon to enable
    Log    Enabling addon: ${addon_name}
    addon_keywords.enable_addon    ${addon_name}
    Log    Addon ${addon_name} enable request sent

Disable Addon
    [Arguments]    ${addon_name}
    [Documentation]    Disable an addon
    ...               Args:
    ...                   addon_name: Name of the addon to disable
    Log    Disabling addon: ${addon_name}
    addon_keywords.disable_addon    ${addon_name}
    Log    Addon ${addon_name} disable request sent

Wait For Addon Enabled
    [Arguments]    ${addon_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until addon is enabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for addon ${addon_name} to be enabled (timeout: ${timeout}s)
    addon_keywords.wait_for_addon_enabled    ${addon_name}    ${timeout}
    Log    Addon ${addon_name} is now enabled

Wait For Addon Disabled
    [Arguments]    ${addon_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until addon is disabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for addon ${addon_name} to be disabled (timeout: ${timeout}s)
    addon_keywords.wait_for_addon_disabled    ${addon_name}    ${timeout}
    Log    Addon ${addon_name} is now disabled

Is Addon Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Check if addon is enabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...               Returns:
    ...                   bool: True if enabled, False otherwise
    ${is_enabled}=    addon_keywords.is_addon_enabled    ${addon_name}
    RETURN    ${is_enabled}

Wait For Monitoring Pods Running
    [Arguments]    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for monitoring pods (Prometheus, Grafana) to be running
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for monitoring pods in namespace ${namespace} to be running
    addon_keywords.wait_for_monitoring_pods_running    ${namespace}    ${timeout}
    Log    Monitoring pods are now running

Wait For Addon Pods Running
    [Arguments]    ${namespace}    ${label}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for pods matching label to be running in namespace
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   label: Label selector for pods
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for pods with label ${label} in namespace ${namespace} to be running
    addon_keywords.wait_for_pods_running    ${namespace}    ${label}    ${timeout}
    Log    Pods with label ${label} are running in ${namespace}

Wait For Addon Service Running
    [Arguments]    ${namespace}    ${service_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for service to be running in namespace
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   service_name: Name of the service
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for service ${service_name} in namespace ${namespace} to be running
    addon_keywords.wait_for_service_running    ${namespace}    ${service_name}    ${timeout}
    Log    Service ${service_name} is running in ${namespace}

Configure Nvidia Toolkit Addon
    [Arguments]    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    [Documentation]    Configure the nvidia-driver-toolkit addon with image repo, tag, and driver location
    ...               Args:
    ...                   addon_name: Name of the addon (nvidia-driver-toolkit)
    ...                   image_repo: Image repository
    ...                   image_tag: Image tag
    ...                   driver_location: Driver location path
    Log    Configuring nvidia-driver-toolkit addon: repo=${image_repo}, tag=${image_tag}, driver=${driver_location}
    addon_keywords.configure_nvidia_toolkit_addon    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    Log    Nvidia-driver-toolkit addon configured

Verify Nvidia Toolkit Addon Configured
    [Arguments]    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    [Documentation]    Verify nvidia-driver-toolkit addon configuration is applied
    ...               Args:
    ...                   addon_name: Name of the addon (nvidia-driver-toolkit)
    ...                   image_repo: Expected image repository
    ...                   image_tag: Expected image tag
    ...                   driver_location: Expected driver location path
    Log    Verifying nvidia-driver-toolkit addon configuration
    ${config}=    addon_keywords.get_nvidia_toolkit_addon_config    ${addon_name}
    Should Be Equal    ${config['image_repo']}    ${image_repo}
    ...    message=Expected image repo '${image_repo}', got '${config["image_repo"]}'
    Should Be Equal    ${config['image_tag']}    ${image_tag}
    ...    message=Expected image tag '${image_tag}', got '${config["image_tag"]}'
    Should Be Equal    ${config['driver_location']}    ${driver_location}
    ...    message=Expected driver location '${driver_location}', got '${config["driver_location"]}'
    ${is_configured}=    addon_keywords.verify_nvidia_toolkit_addon_config    ${addon_name}    ${image_repo}    ${image_tag}    ${driver_location}
    Should Be True    ${is_configured}
    ...    message=Nvidia-driver-toolkit addon configuration should match expected values
    Log    Nvidia-driver-toolkit addon configuration verified
Port Forward To Prometheus
    [Arguments]    ${namespace}    ${pod_name}    ${local_port}=9090
    [Documentation]    Port forward to Prometheus pod
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   pod_name: Name of the Prometheus pod
    ...                   local_port: Local port to forward to (default: 9090)
    Log    Port forwarding to Prometheus pod ${pod_name} on port ${local_port}
    addon_keywords.port_forward_to_prometheus    ${namespace}    ${pod_name}    ${local_port}
    Log    Port forward established

Stop Prometheus Port Forward
    [Documentation]    Stop port forwarding
    Log    Stopping port forward
    addon_keywords.stop_port_forward
    Log    Port forward stopped

Query Prometheus
    [Arguments]    ${query}    ${prometheus_url}=http://localhost:9090
    [Documentation]    Query Prometheus for metrics
    ...               Args:
    ...                   query: PromQL query string
    ...                   prometheus_url: Prometheus URL (default: http://localhost:9090)
    ...               Returns:
    ...                   dict: Query result
    Log    Querying Prometheus: ${query}
    ${result}=    addon_keywords.query_prometheus    ${query}    ${prometheus_url}
    Log    Prometheus query successful
    RETURN    ${result}

Verify Prometheus Metric Exists
    [Arguments]    ${query}    ${prometheus_url}=http://localhost:9090
    [Documentation]    Verify that a Prometheus metric exists
    ...               Args:
    ...                   query: PromQL query string
    ...                   prometheus_url: Prometheus URL (default: http://localhost:9090)
    ...               Returns:
    ...                   bool: True if metric exists and has data
    Log    Verifying Prometheus metric: ${query}
    ${exists}=    addon_keywords.verify_prometheus_metric_exists    ${query}    ${prometheus_url}
    Should Be True    ${exists}    Metric ${query} should exist
    Log    Metric ${query} verified successfully

Restore Addon State
    [Arguments]    ${addon_name}    ${initial_state}
    [Documentation]    Restore addon to its initial state
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   initial_state: Initial state (True for enabled, False for disabled)
    Log    Restoring addon ${addon_name} to initial state: ${initial_state}
    addon_keywords.restore_addon_state    ${addon_name}    ${initial_state}
    Log    Addon ${addon_name} restored to initial state

# BDD Keywords for Addon Tests
Initial Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store the initial state of the addon
    ${initial_state}=    Get Addon Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_MONITORING}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

Monitoring Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the monitoring addon and wait for deployment
    ${is_enabled}=    Is Addon Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Enable Addon    ${addon_name}
    Wait For Addon Enabled    ${addon_name}    timeout=900
    Log    Monitoring addon ${addon_name} is enabled

Monitoring Pods Should Be Running
    [Arguments]    ${namespace}
    [Documentation]    Verify monitoring pods are running
    Wait For Monitoring Pods Running    ${namespace}    timeout=900
    Log    All monitoring pods are running in ${namespace}

Prometheus Should Be Accessible
    [Arguments]    ${namespace}
    [Documentation]    Setup port-forward and verify Prometheus is accessible
    ${prometheus_pod}=    Get Prometheus Pod Name
    Port Forward To Prometheus    ${namespace}    ${prometheus_pod}    ${LOCAL_PROMETHEUS_PORT}
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
        Verify Prometheus Metric Exists    ${metric}
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
    Run Keyword And Ignore Error    Stop Prometheus Port Forward
    
    # Restore addon to initial state
    Run Keyword If    '${INITIAL_STATE_MONITORING}' != 'None'
    ...    Restore Addon State    ${ADDON_MONITORING}    ${INITIAL_STATE_MONITORING}
    
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
    ${initial_state}=    Get Addon Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_PCIDEVICES}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

PCI Devices Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the pcidevices-controller addon and wait for deployment
    ${is_enabled}=    Is Addon Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    Enable Addon    ${addon_name}
    Wait For Addon Enabled    ${addon_name}    timeout=900
    Log    PCI Devices addon ${addon_name} is enabled

PCI Devices Controller Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify pcidevices-controller pods are running
    Wait For Addon Pods Running    ${namespace}    ${label}    timeout=900
    Log    All pcidevices-controller pods are running in ${namespace}

PCI Devices Webhook Service Should Be Running
    [Arguments]    ${namespace}    ${service_name}
    [Documentation]    Verify pcidevices-webhook service is running
    Wait For Addon Service Running    ${namespace}    ${service_name}    timeout=300
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
    ...    Restore Addon State    ${ADDON_PCIDEVICES}    ${INITIAL_STATE_PCIDEVICES}
    Cleanup test resources
    Log    Suite teardown completed
