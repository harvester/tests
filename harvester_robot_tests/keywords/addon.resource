*** Settings ***
Documentation    Addon Keywords - Reusable keywords for addon operations
Library          ../libs/keywords/addon_keywords.py
Resource         variables.resource

*** Keywords ***
Get Addon Initial State
    [Arguments]    ${addon_name}
    [Documentation]    Get initial state of addon (enabled/disabled)
    ...               Args:
    ...                   addon_name: Name of the addon
    ...               Returns:
    ...                   bool: True if enabled, False if disabled
    Log    Getting initial state of addon: ${addon_name}
    ${initial_state}=    get_addon_initial_state    ${addon_name}
    Log    Addon ${addon_name} initial state: ${initial_state}
    RETURN    ${initial_state}

Enable Addon
    [Arguments]    ${addon_name}
    [Documentation]    Enable an addon
    ...               Args:
    ...                   addon_name: Name of the addon to enable
    Log    Enabling addon: ${addon_name}
    enable_addon    ${addon_name}
    Log    Addon ${addon_name} enable request sent

Disable Addon
    [Arguments]    ${addon_name}
    [Documentation]    Disable an addon
    ...               Args:
    ...                   addon_name: Name of the addon to disable
    Log    Disabling addon: ${addon_name}
    disable_addon    ${addon_name}
    Log    Addon ${addon_name} disable request sent

Wait For Addon Enabled
    [Arguments]    ${addon_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until addon is enabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for addon ${addon_name} to be enabled (timeout: ${timeout}s)
    wait_for_addon_enabled    ${addon_name}    ${timeout}
    Log    Addon ${addon_name} is now enabled

Wait For Addon Disabled
    [Arguments]    ${addon_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until addon is disabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for addon ${addon_name} to be disabled (timeout: ${timeout}s)
    wait_for_addon_disabled    ${addon_name}    ${timeout}
    Log    Addon ${addon_name} is now disabled

Is Addon Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Check if addon is enabled
    ...               Args:
    ...                   addon_name: Name of the addon
    ...               Returns:
    ...                   bool: True if enabled, False otherwise
    ${is_enabled}=    is_addon_enabled    ${addon_name}
    RETURN    ${is_enabled}

Wait For Monitoring Pods Running
    [Arguments]    ${namespace}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for monitoring pods (Prometheus, Grafana) to be running
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for monitoring pods in namespace ${namespace} to be running
    wait_for_monitoring_pods_running    ${namespace}    ${timeout}
    Log    Monitoring pods are now running

Port Forward To Prometheus
    [Arguments]    ${namespace}    ${pod_name}    ${local_port}=9090
    [Documentation]    Port forward to Prometheus pod
    ...               Args:
    ...                   namespace: Kubernetes namespace
    ...                   pod_name: Name of the Prometheus pod
    ...                   local_port: Local port to forward to (default: 9090)
    Log    Port forwarding to Prometheus pod ${pod_name} on port ${local_port}
    port_forward_to_prometheus    ${namespace}    ${pod_name}    ${local_port}
    Log    Port forward established

Stop Port Forward
    [Documentation]    Stop port forwarding
    Log    Stopping port forward
    stop_port_forward
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
    ${result}=    query_prometheus    ${query}    ${prometheus_url}
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
    ${exists}=    verify_prometheus_metric_exists    ${query}    ${prometheus_url}
    Should Be True    ${exists}    Metric ${query} should exist
    Log    Metric ${query} verified successfully

Restore Addon State
    [Arguments]    ${addon_name}    ${initial_state}
    [Documentation]    Restore addon to its initial state
    ...               Args:
    ...                   addon_name: Name of the addon
    ...                   initial_state: Initial state (True for enabled, False for disabled)
    Log    Restoring addon ${addon_name} to initial state: ${initial_state}
    restore_addon_state    ${addon_name}    ${initial_state}
    Log    Addon ${addon_name} restored to initial state
