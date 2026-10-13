*** Settings ***
Documentation    StorageClass Keywords
Library          ../libs/keywords/storage_keywords.py
Resource         variables.resource


*** Keywords ***
Create LVM Storage Class
    [Arguments]    ${name}    ${vg_name}    ${vg_type}    ${node}
    storage_keywords.create_lvm_storageclass    ${name}    ${vg_name}    ${vg_type}    ${node}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Storage Class Is Present    ${name}

Create Storage Class
    [Arguments]    ${name}    ${data_engine}    ${number_of_replicas}    ${disk_selector}
    [Documentation]    Create a StorageClass with Longhorn provisioner.
    ...    disk_selector can be a comma-separated list (e.g. lhv2,fast).
    storage_keywords.create_storageclass    ${name}    ${data_engine}    ${number_of_replicas}    ${disk_selector}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Storage Class Is Present    ${name}

Create LHv2 Storage Class
    [Arguments]    ${name}    ${number_of_replicas}    ${disk_selector}
    Create Storage Class    ${name}    v2    ${number_of_replicas}    ${disk_selector}

Delete Storage Class
    [Arguments]    ${name}
    storage_keywords.delete_storageclass    ${name}

Storage Class Is Present
    [Arguments]    ${name}
    ${sc}=    storage_keywords.get_storageclass    ${name}
    Should Not Be Empty    ${sc}

Storage Class Should Not Exist
    [Arguments]    ${name}
    ${sc}=    storage_keywords.get_storageclass    ${name}
    Should Be Equal    ${sc}    ${NONE}    msg=StorageClass ${name} still exists

Wait Until Storage Class Is Deleted
    [Arguments]    ${name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Storage Class Should Not Exist    ${name}

Storage Class Parameter Should Be
    [Arguments]    ${name}    ${key}    ${expected}
    [Documentation]    Assert one entry of the StorageClass' parameters map
    ${sc}=    storage_keywords.get_storageclass    ${name}
    Should Not Be Equal    ${sc}    ${NONE}    msg=StorageClass ${name} does not exist
    Dictionary Should Contain Item    ${sc}[parameters]    ${key}    ${expected}
