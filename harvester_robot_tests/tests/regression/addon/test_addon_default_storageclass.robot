*** Settings ***
Documentation    Addon Webhook - Default StorageClass Validation
...
...             Storage-backed addons (rancher-monitoring, rancher-k3k) require a
...             cluster default StorageClass when being enabled. The webhook introduced
...             in HARV-12112 rejects the request when none is set.
Test Tags        regression    addons    storageclass    webhook    HARV-12112

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/addon.resource
Resource         ../../../keywords/storageclass.resource

Suite Setup      Suite Setup For Default SC Addon Tests
Suite Teardown   Suite Teardown For Default SC Addon Tests

*** Variables ***
${ADDON_MONITORING}      rancher-monitoring
${ADDON_K3K}             rancher-k3k
${DEFAULT_SC_NAME}       ${NONE}

*** Test Cases ***
Test Enable Rancher Monitoring Without Default StorageClass Is Rejected
    [Tags]    p0    negative
    [Documentation]    Enabling rancher-monitoring when no default StorageClass exists
    ...               must be rejected by the webhook with a descriptive error.
    ...               Steps:
    ...                   1. Ensure rancher-monitoring is disabled
    ...                   2. Remove the default StorageClass annotation
    ...                   3. Try to enable rancher-monitoring (no retry)
    ...                   4. Verify the request is rejected and the error names the cause
    [Setup]     Disable Addon If Enabled    ${ADDON_MONITORING}

    Given Default StorageClass Is Removed
    Then Run Keyword And Expect Error    *default StorageClass*
    ...    Enable    ${ADDON_MONITORING}    retries=0

    [Teardown]    Restore Default StorageClass

Test Enable Rancher K3K Without Default StorageClass Is Rejected
    [Tags]    p1    negative
    [Documentation]    Enabling rancher-k3k when no default StorageClass exists
    ...               must be rejected by the webhook.
    ...               Skipped when rancher-k3k is not installed in the cluster.
    [Setup]    Run Keywords
    ...    Skip If Addon Does Not Exist    ${ADDON_K3K}
    ...    AND    Disable Addon If Enabled    ${ADDON_K3K}

    Given Default StorageClass Is Removed
    Then Run Keyword And Expect Error    *default StorageClass*
    ...    Enable    ${ADDON_K3K}    retries=0

    [Teardown]    Restore Default StorageClass

Test Enable Non Storage Backed Addon Without Default StorageClass Is Allowed
    [Tags]    p1
    [Documentation]    Enabling an addon that does not require storage (pcidevices-controller)
    ...               must succeed even when no default StorageClass is set, confirming
    ...               the webhook gate is scoped only to storage-backed addons.
    [Setup]    Run Keywords
    ...    Skip If Addon Does Not Exist    pcidevices-controller
    ...    AND    Disable Addon If Enabled    pcidevices-controller

    Given Default StorageClass Is Removed
    Then Enable    pcidevices-controller    retries=0

    [Teardown]    Run Keywords
    ...    Restore Default StorageClass
    ...    AND    Disable Addon If Enabled    pcidevices-controller

*** Keywords ***
Suite Setup For Default SC Addon Tests
    Set up test environment
    ${sc}=    Get Default Storage Class
    Set Suite Variable    ${DEFAULT_SC_NAME}    ${sc}

Suite Teardown For Default SC Addon Tests
    Run Keyword And Ignore Error    Restore Default StorageClass
    Run Keyword If Any Tests Failed    Log Variables

Default StorageClass Is Removed
    [Documentation]    Remove the default annotation from the current default SC.
    ...               Skips the test if no default SC is set (nothing to unset).
    Skip If    '${DEFAULT_SC_NAME}' == 'None'
    ...    No default StorageClass in the cluster - skipping test
    Unset Default Storage Class    ${DEFAULT_SC_NAME}

Restore Default StorageClass
    Run Keyword If    '${DEFAULT_SC_NAME}' != 'None'
    ...    Set Default Storage Class    ${DEFAULT_SC_NAME}

Disable Addon If Enabled
    [Arguments]    ${addon_name}
    ${enabled}=    Is Enabled    ${addon_name}
    Run Keyword If    ${enabled}    Disable    ${addon_name}
    Run Keyword If    ${enabled}    Wait For Disabled    ${addon_name}    timeout=300

Skip If Addon Does Not Exist
    [Arguments]    ${addon_name}
    ${exists}=    Addon Exists    ${addon_name}
    Skip If    not ${exists}    Addon ${addon_name} not present in this cluster
