*** Settings ***
Documentation    Storage Keywords
Library          ../libs/keywords/storage_keywords.py
Library          ../libs/keywords/vm_keywords.py
Library          ../libs/keywords/volume_keywords.py
Library          Collections
Resource         variables.resource
Resource         common.resource
Resource         host.resource


*** Variables ***
&{DATA_DISK_BY_NODE}    &{EMPTY}
${LHv2_SC_REPLICAS}    ${EMPTY}
${LVM_NODE_COUNT}                ${0}
@{LVM_VOLUMES_CREATED}
&{LVM_DISK_BY_NODE}              &{EMPTY}
&{LVM_VG_NODE_MAP}               &{EMPTY}


*** Keywords ***
# instance-manager (IM)
Standard Nodes Have Running v2 IM Pods
    ${standard_nodes_count}=    host.Count Standard Nodes
    ${running_v2_im_pods_count}=    common.Count Pods By Label
    ...    ${LONGHORN_NAMESPACE}
    ...    longhorn.io/data-engine=v2,longhorn.io/component=instance-manager
    ...    status=Running
    Should Be Equal As Integers    ${running_v2_im_pods_count}    ${standard_nodes_count}

Standard Nodes Have No v2 IM Pods
    ${standard_nodes_count}=    host.Count Standard Nodes
    ${v2_im_pods_count}=    common.Count Pods By Label
    ...    ${LONGHORN_NAMESPACE}
    ...    longhorn.io/data-engine=v2,longhorn.io/component=instance-manager
    Should Be Equal As Integers    ${v2_im_pods_count}    0

# Provision LHv2 Storages
Pick Unprovisioned Data Disks
    [Arguments]    ${namespace}=${LONGHORN_NAMESPACE}
    [Documentation]    Pick usable data disks per standard node as disk name by node name
    &{disk_by_node}=    storage_keywords.pick_unprovisioned_data_disks    ${namespace}
    RETURN    &{disk_by_node}

Cluster Has Available Data Disks And Set Suite Variables
    [Documentation]    Check if there are 1 to 3 unprovisioned data disks
    &{DATA_DISK_BY_NODE}=    Pick Unprovisioned Data Disks
    &{DATA_DISK_BY_NODE}=    Evaluate    dict(list($DATA_DISK_BY_NODE.items())[:3])
    ${data_disks_count}=    Get Length    ${DATA_DISK_BY_NODE}
    Should Be True    ${data_disks_count} >= 1    Cluster has NO available data disk

    Set Suite Variable    &{DATA_DISK_BY_NODE}
    Set Suite Metadata    DATA_DISK_BY_NODE    ${DATA_DISK_BY_NODE}
    Set Suite Variable    ${LHv2_SC_REPLICAS}    ${data_disks_count}
    Set Suite Metadata    LHv2_SC_REPLICAS    ${LHv2_SC_REPLICAS}

Provision Storages With LHv2 Data Engine
    [Arguments]    &{disk_by_node}
    FOR    ${node}    ${disk}    IN    &{disk_by_node}
        Set Test Message    \nProvision blockdevice ${LONGHORN_NAMESPACE}/${disk} with LHv2    append=yes
        storage_keywords.provision_longhorn_storage    ${disk}    LonghornV2    ${LONGHORN_NAMESPACE}
    END

Blockdevice Is Provisioned
    [Arguments]    ${name}    ${namespace}=${LONGHORN_NAMESPACE}
    ${is_provisioned}=    storage_keywords.is_blockdevice_provisioned    ${name}    ${namespace}
    Should Be True    ${is_provisioned}    Blockdevice ${namespace}/${name} is NOT provisioned

Longhorn Node Disk Is ${condition}
    [Arguments]    ${node_name}    ${disk_name}
    [Documentation]    Check Longhorn node disk has the expected condition
    ${cond_status}=    storage_keywords.get_lh_node_disk_status_condition    ${node_name}    ${disk_name}    ${condition}
    Should Be True    ${cond_status}

Wait Until LHv2 Storages Are Provisioned
    [Arguments]    &{disk_by_node}
    [Documentation]    Check provisioned storages are ``Ready``, ``Schedulable`` and ``Provisioned``
    FOR    ${node}    ${disk}    IN    &{disk_by_node}
        Log    Waiting storage ${disk} on node ${node} become ``Ready``, ``Schedulable`` and ``Provisioned``...
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Blockdevice Is Provisioned    ${disk}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Longhorn Node Disk Is Ready    ${node}    ${disk}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Longhorn Node Disk Is Schedulable    ${node}    ${disk}
    END

# LVM Suite Setup Keywords
Identify And Assign LVM Disks
    [Documentation]    Identify nodes with at least one additional disk >= 50 GiB for LVM.
    ...               Single-node cluster: needs 1 such node (creates vg-dm-thin only).
    ...               Multi-node cluster: randomly picks 2 nodes (vg-dm-thin + vg-dm-striped).
    ...               Skips the entire suite when no eligible nodes are found.
    Log    Identifying disks suitable for LVM (>= 50 GiB)
    &{LVM_DISK_BY_NODE}=    storage_keywords.identify_lvm_suitable_disks    ${50}
    ${node_count}=    Get Length    ${LVM_DISK_BY_NODE}
    Skip If    ${node_count} == 0
    ...    No nodes found with a suitable disk >= 50 GiB — LVM tests require at least 1 eligible node
    Set Suite Variable    &{LVM_DISK_BY_NODE}
    Set Suite Variable    ${LVM_NODE_COUNT}    ${node_count}
    Log    Found ${node_count} node(s) with LVM-suitable disks: ${LVM_DISK_BY_NODE}

Create LVM Volume Groups
    [Documentation]    Create volume groups from identified disks.
    ...               Single-node: creates the VG matching ${LVM_VG_TYPE} (dm-thin or striped).
    ...               Multi-node: creates vg-dm-thin + vg-dm-striped on separate nodes.
    Log    Creating LVM volume groups (${LVM_NODE_COUNT} eligible node(s)) type=${LVM_VG_TYPE}
    &{LVM_VG_NODE_MAP}=    storage_keywords.create_lvm_volume_groups    ${LVM_DISK_BY_NODE}    ${LVM_VG_TYPE}
    Set Suite Variable    &{LVM_VG_NODE_MAP}
    # Map the two accepted values to canonical VG/SC names and VM/VOL suffix
    ${_vg_name}=    Set Variable If    '${LVM_VG_TYPE}' == 'dm-thin'    vg-dm-thin    vg-dm-striped
    ${_sc_name}=    Set Variable If    '${LVM_VG_TYPE}' == 'dm-thin'    lvm-sc-dm-thin    lvm-sc-dm-striped
    ${_suffix}=    Set Variable If    '${LVM_VG_TYPE}' == 'dm-thin'    thin    striped
    Set Suite Variable    ${LVM_VG_ACTIVE}    ${_vg_name}
    Set Suite Variable    ${LVM_SC_ACTIVE}    ${_sc_name}
    Set Suite Variable    ${LVM_VM_BLOCK}    lvm-vm-block-${_suffix}
    Set Suite Variable    ${LVM_VM_FS}    lvm-vm-fs-${_suffix}
    Set Suite Variable    ${LVM_VM_SC}    lvm-vm-sc-${_suffix}
    Set Suite Variable    ${LVM_VOL_BLOCK}    lvm-vol-block-${_suffix}
    Set Suite Variable    ${LVM_VOL_FS}    lvm-vol-fs-${_suffix}
    Log    LVM volume groups created: ${LVM_VG_NODE_MAP}
    Log    Active config: VG=${_vg_name} SC=${_sc_name} VM/VOL suffix=${_suffix}

# LVM Volume Keywords
LVM Block Volume Is Created
    [Arguments]    ${vol_name}    ${size}    ${sc_name}
    [Documentation]    Create a block volume using the LVM StorageClass
    Log    Creating LVM block volume ${vol_name} size=${size} sc=${sc_name}
    volume_keywords.create_volume    ${vol_name}    ${size}    storage_class=${sc_name}    volume_mode=Block
    Append To List    ${LVM_VOLUMES_CREATED}    ${vol_name}
    Set Suite Variable    @{LVM_VOLUMES_CREATED}
    Log    LVM block volume ${vol_name} created

LVM Filesystem Volume Is Created
    [Arguments]    ${vol_name}    ${size}    ${sc_name}
    [Documentation]    Create a filesystem volume using the LVM StorageClass
    Log    Creating LVM filesystem volume ${vol_name} size=${size} sc=${sc_name}
    volume_keywords.create_volume    ${vol_name}    ${size}    storage_class=${sc_name}    volume_mode=Filesystem
    Append To List    ${LVM_VOLUMES_CREATED}    ${vol_name}
    Set Suite Variable    @{LVM_VOLUMES_CREATED}
    Log    LVM filesystem volume ${vol_name} created

# LVM Volume Expand Keywords
LVM Volume Is Expanded Directly
    [Arguments]    ${vol_name}    ${new_size}
    [Documentation]    Expand LVM volume by editing the volume directly
    Log    Expanding volume ${vol_name} to ${new_size} via volume edit
    volume_keywords.expand_lvm_pvc    ${vol_name}    ${new_size}
    Log    Volume ${vol_name} expanded to ${new_size}

# LVM Cleanup
Cleanup LVM Test Resources
    [Documentation]    Cleanup all LVM test resources
    Log    Cleaning up LVM test resources
    # Delete VMs and root disk and wait for full termination before releasing volumes
    FOR    ${vm_name}    IN    @{VMS_CREATED}
        Run Keyword And Ignore Error    vm_keywords.delete_vm    ${vm_name}
        Run Keyword And Ignore Error    vm_keywords.wait_for_vm_deleted    ${vm_name}
        Run Keyword And Ignore Error    volume_keywords.delete_volume    ${vm_name}-disk-0
    END
    # Delete restored VMs (from snapshot restore to new VM tests)
    FOR    ${vm_name}    IN    @{VMS_RESTORED}
        Run Keyword And Ignore Error    vm_keywords.delete_vm    ${vm_name}
        Run Keyword And Ignore Error    vm_keywords.wait_for_vm_deleted    ${vm_name}
        Run Keyword And Ignore Error    volume_keywords.delete_volume    ${vm_name}-disk-0
    END

    # Delete Volumes
    FOR    ${vol_name}    IN    @{LVM_VOLUMES_CREATED}
        Run Keyword And Ignore Error    volume_keywords.delete_volume    ${vol_name}
    END
    # Delete StorageClasses
    FOR    ${sc_name}    IN    @{LVM_SCS_CREATED}
        Run Keyword And Ignore Error    storage_keywords.delete_lvm_storage_class    ${sc_name}
    END
    # Remove volume groups
    Run Keyword And Ignore Error    storage_keywords.cleanup_lvm_volume_groups    ${LVM_DISK_BY_NODE}
    Log    LVM test resources cleaned up
