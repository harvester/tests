*** Settings ***
Documentation    StorageClass Keywords
Library          ../libs/keywords/storage_keywords.py
Resource         variables.resource
Resource         setting.resource
Resource         storage.resource


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

Create LHv2 Storage Class With Provisioned Disks
    [Arguments]    ${name}
    [Documentation]    Enable the LHv2 data engine if needed, reuse provisioned LHv2 disks
    ...    (or provision free NVMe disks) and create an LHv2 StorageClass.
    ...    Returns the disks provisioned here (empty if existing ones were reused).
    ${is_enabled}=    Run Keyword And Return Status    setting.LHv2 Data Engine Is Enabled
    IF    not ${is_enabled}
        setting.Enable LHv2 Data Engine
        setting.Wait Until LHv2 Data Engine Is Enabled
    END
    # Reuse provisioned LHv2 disks, provision a free NVMe disk only if there is none
    &{provisioned}=    Create Dictionary
    &{disk_by_node}=    storage.Get Provisioned LHv2 Disks
    IF    not $disk_by_node
        &{disk_by_node}=    storage.Get Available NVMe Disks
        # Record the selection first, so a failure below can roll it back
        &{provisioned}=    Set Variable    ${disk_by_node}
    END
    TRY
        IF    $provisioned
            Provision Storages With LHv2 Data Engine    ${provisioned}
        END
        Wait Until Storages Are Provisioned    ${disk_by_node}
        # No disk selector: v2 volumes only land on v2 disks anyway
        ${replicas}=    Get Length    ${disk_by_node}
        Create LHv2 Storage Class    ${name}    ${replicas}    ${EMPTY}
    EXCEPT    AS    ${error}
        # The caller never gets the disk map, so release what was provisioned here
        Run Keyword And Ignore Error    Unprovision Storages    ${provisioned}
        Fail    ${error}
    END
    RETURN    ${provisioned}
