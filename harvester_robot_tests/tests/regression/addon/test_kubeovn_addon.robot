*** Settings ***
Documentation    KubeOVN Addon Test Cases
...              This suite tests the enable, disable and basic status
...              of the KubeOVN add-on in Harvester.
Test Tags        regression    addons    kubeovn

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/addon.resource
Resource         ../../../keywords/kubeovn.resource

Suite Setup      Suite Setup For KubeOVN Addon Tests
Suite Teardown   Suite Teardown For KubeOVN Addon Tests

*** Variables ***
${ADDON_KUBEOVN}               kubeovn-operator
${INITIAL_STATE_KUBEOVN}       ${None}
${KUBEOVN_NAMESPACE}           kube-system
${KUBEOVN_CONTROLLER_LABEL}    app=kube-ovn-controller
${KUBEOVN_MONITOR_LABEL}       app=kube-ovn-monitor
${KUBEOVN_WEBHOOK_LABEL}       app=kube-ovn-webhook
${DEFAULT_VPC_NAME}            ovn-cluster

*** Test Cases ***
Test KubeOVN Addon End-to-End
    [Tags]    p0    coretest    kubeovn
    [Documentation]    Verify KubeOVN addon can be enabled, configured and basic functionality works
    ...                Steps:
    ...                    1. Store initial state of kubeovn-operator addon
    ...                    2. Enable kubeovn-operator addon and wait for deployment
    ...                Expected Result:
    ...                    - Addons restored to initial state after test

    # Step 1: Store initial state of KubeOVN addon
    Given Initial KubeOVN Addon State Is Captured    ${ADDON_KUBEOVN}

    # Step 2: Enable KubeOVN Addon
    When KubeOVN Addon is Enabled    ${ADDON_KUBEOVN}

    # Step 3: Verify controller pods are running
    Then KubeOVN Controller Pods Should Be Running
    ...    ${KUBEOVN_NAMESPACE}
    ...    ${KUBEOVN_CONTROLLER_LABEL}

    # Step 4: Verify controller pods are running
    Then KubeOVN Monitor Pods Should Be Running
    ...    ${KUBEOVN_NAMESPACE}
    ...    ${KUBEOVN_CONTROLLER_LABEL}

    # Step 5: Verify controller pods are running
    Then KubeOVN Webhook Pods Should Be Running
    ...    ${KUBEOVN_NAMESPACE}
    ...    ${KUBEOVN_CONTROLLER_LABEL}

    Then KubeOVN VPC Should Exist    ${DEFAULT_VPC_NAME}

*** Keywords ***
Suite Setup For KubeOVN Addon Tests
    [Documentation]    Initialize test environment for kubeovn addon tests
    Log    Setting up test environment for kubeovn addon tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For KubeOVN Addon Tests
    [Documentation]    Cleanup and restore kubeovn addon state after tests
    Log    Running suite teardown for kubeovn addon tests
    Run Keyword If    '${INITIAL_STATE_KUBEOVN}' != 'None'
    ...    addon.Restore State    ${ADDON_KUBEOVN}    ${INITIAL_STATE_KUBEOVN}
    Cleanup test resources
    Log    Suite teardown completed

KubeOVN Controller Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify kubeovn-controller pods are running
    addon.Wait For Pods Running    ${namespace}    ${label}    timeout=900
    Log    All kubeovn-controller pods are running in ${namespace}

KubeOVN Monitor Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify kubeovn-monitor pods are running
    addon.Wait For Pods Running    ${namespace}    ${label}    timeout=900
    Log    All kubeovn-monitor pods are running in ${namespace}

KubeOVN Webhook Pods Should Be Running
    [Arguments]    ${namespace}    ${label}
    [Documentation]    Verify kubeovn-webhook pods are running
    addon.Wait For Pods Running    ${namespace}    ${label}    timeout=900
    Log    All kubeovn-webhook pods are running in ${namespace}
