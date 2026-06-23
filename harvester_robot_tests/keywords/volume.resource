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

# lifecycle
Create Volume
    [Arguments]    ${vol_name}    ${size}=${DEFAULT_VOLUME_SIZE}    ${storage_class}=${DEFAULT_STORAGE_CLASS}    ${replicas}=${DEFAULT_VM_REPLICAS}
    [Documentation]    Create a volume (PVC) backed by the given storage class
    volume_keywords.create_volume    ${vol_name}    ${size}    ${replicas}    blockdev    storage_class=${storage_class}

Create ${size_gi}Gi Volume
    [Arguments]    ${vol_name}
    Create Volume    ${vol_name}    ${size_gi}Gi

Delete Volume
    [Arguments]    ${vol_name}
    volume_keywords.delete_volume    ${vol_name}

Wait Until Volume Is Deleted
    [Arguments]    ${vol_name}
    volume_keywords.wait_for_volume_deleted    ${vol_name}

Volume Is Present
    [Arguments]    ${vol_name}
    ${status}=    volume_keywords.get_volume_status    ${vol_name}
    Should Not Be Empty    ${status}

Volume Should Be Listed
    [Arguments]    ${vol_name}
    ${volumes}=    volume_keywords.list_volumes
    ${names}=    Evaluate    [v['metadata']['name'] for v in $volumes]
    Should Contain    ${names}    ${vol_name}

# snapshot
Create Volume Snapshot
    [Arguments]    ${vol_name}    ${snapshot_name}    ${snapshot_class}=longhorn-snapshot
    volume_keywords.create_volume_snapshot    ${vol_name}    ${snapshot_name}    ${snapshot_class}

Wait Until Snapshot Is Ready
    [Arguments]    ${snapshot_name}
    volume_keywords.wait_for_snapshot_ready    ${snapshot_name}

Delete Volume Snapshot
    [Arguments]    ${vol_name}    ${snapshot_name}
    volume_keywords.delete_volume_snapshot    ${vol_name}    ${snapshot_name}

Restore Volume From Snapshot
    [Arguments]    ${vol_name}    ${snapshot_name}    ${new_vol_name}
    volume_keywords.restore_volume_from_snapshot    ${vol_name}    ${snapshot_name}    ${new_vol_name}
