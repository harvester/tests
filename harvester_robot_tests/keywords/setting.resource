*** Settings ***
Documentation    Setting Keywords
Library          ../libs/keywords/setting_keywords.py
Resource         variables.resource
Resource         storage.resource


*** Variables ***
${LHv2_SETTING_ID}    longhorn-v2-data-engine-enabled


*** Keywords ***
Enable
    [Arguments]    ${setting_id}
    [Documentation]    Enable setting by ID
    ${setting}=    setting_keywords.enable    ${setting_id}
    Sleep    ${SLEEP_TIMEOUT}    Buffer time before checking
    RETURN    ${setting}

Configured Message Should Be None
    [Arguments]    ${setting_id}
    [Documentation]    Assert configured condition message is None
    ${configured_msg}=    setting_keywords.get_condition_message    ${setting_id}    configured
    Should Be Equal    ${configured_msg}    ${None}

Is Disabled
    [Arguments]    ${setting_id}
    [Documentation]    Assert setting is disabled
    ${value}=    setting_keywords.get_value  ${setting_id}
    Should Not Be Equal    ${value}    true
    Configured Message Should Be None    ${setting_id}

Is Enabled
    [Arguments]    ${setting_id}
    [Documentation]    Assert setting is enabled
    ${value}=    setting_keywords.get_value  ${setting_id}
    Should Be Equal    ${value}    true
    Configured Message Should Be None    ${setting_id}

# longhorn-v2-data-engine-enabled
Enable LHv2 Data Engine
    [Documentation]    Enable Setting ``${LHv2_SETTING_ID}``
    Enable    ${LHv2_SETTING_ID}

LHv2 Data Engine Is Disabled
    [Documentation]    Check Setting ``${LHv2_SETTING_ID}`` is ``false`` and no v2 pods
    Is Disabled    ${LHv2_SETTING_ID}
    storage.Standard Nodes Have No v2 IM Pods

LHv2 Data Engine Is Enabled
    [Documentation]    Check Setting ``${LHv2_SETTING_ID}`` is ``true`` and v2 pods are running
    Is Enabled    ${LHv2_SETTING_ID}
    storage.Standard Nodes Have Running v2 IM Pods

Wait Until LHv2 Data Engine Is Enabled
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    LHv2 Data Engine Is Enabled