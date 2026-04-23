*** Settings ***
Documentation    Rancher-Monitoring Addon Test Cases
...             This suite tests the enable, disable, and basic functionality
...             of the Rancher-Monitoring add-on in Harvester.
Test Tags        regression    addons    rancher-monitoring

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
    [Teardown]    addon.Stop Port Forward

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



