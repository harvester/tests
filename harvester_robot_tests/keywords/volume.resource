*** Settings ***
Documentation    Volume Keywords
Library          ../libs/keywords/volume_keywords.py
Resource         variables.resource

*** Keywords ***
Create Volume
    [Arguments]    ${volume_name}    ${size}=2Gi    ${replicas}=3    ${frontend}=blockdev
    [Documentation]    Create a volume
    volume_keywords.create_volume    ${volume_name}    ${size}    ${replicas}    ${frontend}

Delete Volume
    [Arguments]    ${volume_name}    ${wait}=${True}
    [Documentation]    Delete a volume
    volume_keywords.delete_volume    ${volume_name}    ${wait}

Wait For Volume Deleted
    [Arguments]    ${volume_name}    ${timeout}=${DEFAULT_TIMEOUT_SHORT}
    [Documentation]    Wait for a volume to be deleted
    volume_keywords.wait_for_volume_deleted    ${volume_name}    ${timeout}

Cleanup Volumes
    [Documentation]    Delete all test-labeled PVCs
    volume_keywords.cleanup_volumes
