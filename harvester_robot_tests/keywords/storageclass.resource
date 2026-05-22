*** Settings ***
Documentation    StorageClass Keywords
Library          ../libs/keywords/storage_keywords.py
Library          Collections
Resource         variables.resource


*** Variables ***
@{LVM_SCS_CREATED}


*** Keywords ***
LVM StorageClass Is Created
    [Arguments]    ${sc_name}    ${vg_name}    ${vg_type}
    [Documentation]    Create an LVM StorageClass with specified volume group
    ...               Args:
    ...                   sc_name: Name of the StorageClass
    ...                   vg_name: Volume group name
    ...                   vg_type: Volume group type (dm-thin or striped)
    Log    Creating LVM StorageClass ${sc_name} for VG ${vg_name} type ${vg_type}
    ${node}=    storage_keywords.get_node_for_vg    ${vg_name}    ${LVM_VG_NODE_MAP}
    storage_keywords.create_lvm_storage_class    ${sc_name}    ${vg_name}    ${vg_type}    ${node}
    Append To List    ${LVM_SCS_CREATED}    ${sc_name}
    Set Suite Variable    @{LVM_SCS_CREATED}
    Log    LVM StorageClass ${sc_name} created successfully
