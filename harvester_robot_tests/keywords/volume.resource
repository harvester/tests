*** Settings ***
Documentation    Volume Keywords
Resource         variables.resource
Library          ../libs/keywords/volume_keywords.py

*** Keywords ***
# size
Get Volume Size
    [Arguments]    ${vol_name}
    ${status}=    volume_keywords.get_volume_status    ${vol_name}
    RETURN    ${status["capacity"]["storage"]}

Volume Size Is ${size_gi}Gi
    [Arguments]    ${vol_name}
    ${actual_size}=    Get Volume Size    ${vol_name}
    Should Be Equal As Strings    ${actual_size}    ${size_gi}Gi

Update Volume Size to ${new_size}Gi
    [Arguments]    ${vol_name}
    volume_keywords.expand_volume    ${vol_name}    ${new_size}Gi

# status
Volume Phase Is ${phase}
    [Arguments]    ${vol_name}
    ${status}=    volume_keywords.get_volume_status    ${vol_name}
    Should Be Equal As Strings    ${status["phase"]}    ${phase}

Volume State Is Ready/In-use
    [Arguments]    ${vol_name}
    ${status}=    volume_keywords.get_volume_status    ${vol_name}
    Should Be Empty    ${status["conditions"]}

Wait Until Volume Is Active
    [Arguments]    ${vol_name}
    Sleep    ${SLEEP_TIMEOUT}s    reason=Buffer time for volume changes
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Volume Phase Is Bound    ${vol_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Volume State Is Ready/In-use    ${vol_name}
