*** Settings ***
Documentation    KubeOVN Keywords - Reusable keywords for KubeOVN operations
Library          ../libs/keywords/kubeovn_vpc_keywords.py
Library          ../libs/keywords/kubeovn_subnet_keywords.py
Library          Process
Resource         variables.resource
Resource         common.resource
Resource         addon.resource

*** Keywords ***

Initial KubeOVN Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store initial state of the addon
    ${initial_state}=    addon.Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_KUBEOVN}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

KubeOVN Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the KubeOVN addon and wait for deployment
    ${is_enabled}=    addon.Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    addon.Enable    ${addon_name}
    addon.Wait For Enabled    ${addon_name}    timeout=900
    Log    KubeOVN addon ${addon_name} is enabled

KubeOVN VPC Should Exist
    [Arguments]    ${vpc_name}
    [Documentation]    Check hat the KubeOVN VPC vpc_name exists
    ${vpc}=    kubeovn_vpc_keywords.Get VPC    ${vpc_name}
    Should Not Be Empty    ${vpc}

KubeOVN Subnet Should Exist
    [Arguments]    ${subnet_name}
    [Documentation]    Check hat the KubeOVN Subnet subnet_name exists
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${subnet_name}
    Should Not Be Empty    ${subnet}
