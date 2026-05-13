*** Settings ***
Documentation    Storage Keywords
Library          ../libs/keywords/storage_keywords.py
Resource         variables.resource
Resource         common.resource
Resource         host.resource


*** Variables ***
&{DATA_DISK_BY_NODE}    &{EMPTY}
${LHv2_SC_REPLICAS}    ${EMPTY}


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
