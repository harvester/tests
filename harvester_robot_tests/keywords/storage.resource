*** Settings ***
Documentation    Storage Keywords
Library          ../libs/keywords/storage_keywords.py
Resource         variables.resource
Resource         common.resource
Resource         host.resource


*** Keywords ***
Get LVM Suitable Disks
    [Arguments]    ${min_size_gib}=50
    ${disks}=    storage_keywords.identify_lvm_suitable_disks    ${min_size_gib}
    Should Not Be Empty    ${disks}    No unprovisioned disk >= ${min_size_gib} GiB is available for LVM
    RETURN    ${disks}

Label LVM Test Disks
    [Arguments]    ${disk_by_node}    ${run_id}
    storage_keywords.label_lvm_test_disks    ${disk_by_node}    ${run_id}

Get LVM Test Disks
    [Arguments]    ${run_id}
    ${disks}=    storage_keywords.get_lvm_test_disks    ${run_id}
    RETURN    ${disks}

Find LVM Volume Group Node
    [Arguments]    ${run_id}    ${vg_name}
    ${node}=    storage_keywords.find_lvm_vg_node    ${run_id}    ${vg_name}
    RETURN    ${node}

Get LVM Volume Group Node
    [Arguments]    ${run_id}    ${vg_name}
    ${node}=    storage_keywords.get_lvm_vg_node    ${run_id}    ${vg_name}
    RETURN    ${node}

Create LVM Volume Groups
    [Arguments]    ${disk_by_node}    ${vg_type}=dm-thin
    ${vg_node_map}=    storage_keywords.create_lvm_volume_groups    ${disk_by_node}    ${vg_type}
    RETURN    ${vg_node_map}

Cleanup LVM Volume Groups
    [Arguments]    ${disk_by_node}
    storage_keywords.cleanup_lvm_volume_groups    ${disk_by_node}

# instance-manager (IM)
Standard Nodes Have Running v2 IM Pods
    ${standard_nodes_count}=    host.Count Standard Nodes
    ${running_v2_im_pods_count}=    common.Count Pods By Label
    ...    ${LONGHORN_NAMESPACE}
    ...    longhorn.io/data-engine=v2,longhorn.io/component=instance-manager
    ...    status=Running
    Should Be Equal As Integers    ${running_v2_im_pods_count}    ${standard_nodes_count}

Standard Nodes Have No v2 IM Pods
    ${v2_im_pods_count}=    common.Count Pods By Label
    ...    ${LONGHORN_NAMESPACE}
    ...    longhorn.io/data-engine=v2,longhorn.io/component=instance-manager
    Should Be Equal As Integers    ${v2_im_pods_count}    0

# Provision LHv2 Storages
Get Available NVMe Disks
    [Documentation]    Check if there are 1 to 3 unprovisioned data disks
    &{node_nvme_map}=    storage_keywords.pick_unprovisioned_nvme_disks    ${LONGHORN_NAMESPACE}
    &{node_nvme_map}=    Evaluate    dict(list($node_nvme_map.items())[:3])
    ${nvme_count}=    Get Length    ${node_nvme_map}
    Should Be True    ${nvme_count} >= 1    Cluster has NO available data disk
    RETURN    &{node_nvme_map}

Provision Storages
    [Arguments]    ${engine}    ${disk_by_node}
    FOR    ${node}    ${disk}    IN    &{disk_by_node}
        Log    Provision blockdevice ${LONGHORN_NAMESPACE}/${disk} with ${engine}
        storage_keywords.provision_longhorn_storage    ${disk}    ${engine}    ${LONGHORN_NAMESPACE}
    END

Get Provisioned LHv2 Disks
    [Documentation]    Map of node -> blockdevice for already provisioned LHv2 disks
    &{disk_by_node}=    storage_keywords.get_provisioned_lhv2_disks    ${LONGHORN_NAMESPACE}
    RETURN    &{disk_by_node}

Provision Storages With LHv2 Data Engine
    [Arguments]    ${disk_by_node}
    Provision Storages    LonghornV2    ${disk_by_node}

Unprovision Storages
    [Arguments]    ${disk_by_node}
    [Documentation]    Release the disks and wait until they are free again. Retried, because
    ...    the webhook rejects it while the disk holds the last replica of a volume being deleted.
    FOR    ${node}    ${disk}    IN    &{disk_by_node}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    storage_keywords.unprovision_longhorn_storage    ${disk}    ${LONGHORN_NAMESPACE}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    Blockdevice Is Unprovisioned    ${disk}
    END

Blockdevice Is Unprovisioned
    [Arguments]    ${name}
    ${bd}=    storage_keywords.get_blockdevice    ${name}    ${LONGHORN_NAMESPACE}
    Should Be Equal    ${bd}[status][provisionPhase]    Unprovisioned

Blockdevice Is Provisioned
    [Arguments]    ${name}    ${namespace}=${LONGHORN_NAMESPACE}
    ${is_provisioned}=    storage_keywords.is_blockdevice_provisioned    ${name}    ${namespace}
    Should Be True    ${is_provisioned}    Blockdevice ${namespace}/${name} is NOT provisioned

Longhorn Node Disk Is ${condition}
    [Arguments]    ${node_name}    ${disk_name}
    [Documentation]    Check Longhorn node disk has the expected condition
    ${cond_status}=    storage_keywords.get_lh_node_disk_status_condition    ${node_name}    ${disk_name}    ${condition}
    Should Be True    ${cond_status}

Wait Until Storages Are Provisioned
    [Arguments]    ${disk_by_node}
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
