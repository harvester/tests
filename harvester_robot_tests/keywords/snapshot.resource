*** Settings ***
Documentation    Snapshot Keywords
Resource         variables.resource
Library          ../libs/keywords/snapshot_keywords.py

*** Keywords ***
List Snapshots by prefix
    [Arguments]    ${prefix}    ${namespace}=default
    [Documentation]    List Snapshots whose name starts with the given prefix
    ${snaps}=    snapshot_keywords.list snaps    namespace=${namespace}    name_prefix=${prefix}
    RETURN    ${snaps}

Snapshot is created
    [Arguments]        ${vm_name}    ${snapshot_name}
    [Documentation]    Create a VM snapshot with the given name
    snapshot_keywords.create snapshot    ${vm_name}    ${snapshot_name}

Snapshot should be ready
    [Arguments]        ${snapshot_name}
    [Documentation]    Wait for the snapshot to reach ready state
    snapshot_keywords.wait snapshot ready   ${snapshot_name}

Snapshot is deleted
    [Arguments]        ${snapshot_name}
    [Documentation]    Delete VM snapshot with the given name
    snapshot_keywords.delete snapshot    ${snapshot_name}

Snapshot should be deleted
    [Arguments]        ${snapshot_name}
    [Documentation]    Wait for the snapshot to be deleted
    snapshot_keywords.wait snapshot deleted   ${snapshot_name}
