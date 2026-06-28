*** Settings ***
Documentation    Longhorn V2 Data Engine Test Cases
Test Tags        storage    longhorn    lhv2    experimental

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource
Resource    ../../../keywords/storageclass.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${LHv2_TAG}       lhv2
# Dynamic Variables
&{DISK_BY_NODE}    &{EMPTY}
${SC_REPLICAS}     ${EMPTY}
${SC_NAME}         ${EMPTY}
${IMAGE_NAME}      ${EMPTY}
${VM_NAME}         ${EMPTY}
${VOL_NAME}        ${EMPTY}


*** Test Cases ***
Provision LHv2 Storages
    [Tags]    p0
    [Documentation]    Provision at most 3 NVMe storages with LHv2 Data Engine
    When Provision Storages With LHv2 Data Engine    ${DISK_BY_NODE}
    Then Wait Until Storages Are Provisioned    ${DISK_BY_NODE}

Create LHv2 Storage Class
    [Tags]    p0
    When Tag Storages    ${LHv2_TAG}    ${DISK_BY_NODE}
    Then Create LHv2 Storage Class    ${SC_NAME}    ${SC_REPLICAS}    ${LHv2_TAG}

Create VM With LHv2 Volume
    [Tags]    p0
    Given Storage Class Is Present    ${SC_NAME}
    When Create VM with a 10Gi LHv2 volume    ${VM_NAME}
    Then VM should be running    ${VM_NAME}
    And VM should have IP addresses    ${VM_NAME}
    And Volume size is 10Gi    ${VOL_NAME}

Expand LHv2 Volume Size
    [Tags]    p1
    Given Volume size is 10Gi    ${VOL_NAME}
    When Update volume size to 20Gi    ${VOL_NAME}
    And Wait until volume is active    ${VOL_NAME}
    Then Volume size is 20Gi    ${VOL_NAME}

Expand LHv2 Volume Size From VM
    [Tags]    p1
    Given Volume size is 20Gi    ${VOL_NAME}
    When Update volume size to 30Gi from VM    ${VM_NAME}    ${VOL_NAME}
    And Wait until volume is active   ${VOL_NAME}
    Then Volume size is 30Gi    ${VOL_NAME}


*** Keywords ***
Local Suite Setup
    # Variable initialization
    ${suffix}=    Generate Unique Name    ${LHv2_TAG}
    Set Suite Variable    ${SC_NAME}       sc-${suffix}
    Set Suite Variable    ${IMAGE_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}       vm-${suffix}
    Set Suite Variable    ${VOL_NAME}      vol-${suffix}

    Set up test environment
    # DISK_BY_NODE
    &{nvme_by_node}=    storage.Get Available NVMe Disks
    Set Suite Variable    &{DISK_BY_NODE}    &{nvme_by_node}
    Set Suite Metadata    DISK_BY_NODE    ${DISK_BY_NODE}
    # SC_REPLICAS
    ${nvme_count}=    Get Length    ${DISK_BY_NODE}
    Set Suite Variable    ${SC_REPLICAS}    ${nvme_count}
    Set Suite Metadata    SC_REPLICAS    ${SC_REPLICAS}

    ${is_enabled}=    Run Keyword And Return Status    setting.LHv2 Data Engine Is Enabled
    IF    not ${is_enabled}
        setting.Enable LHv2 Data Engine
        setting.Wait Until LHv2 Data Engine Is Enabled
    END
    Image is available for VM creation   ${IMAGE_NAME}    ${UBUNTU_IMAGE_URL}

Local Suite Teardown
    Common Suite Teardown
    
Create VM With A ${size_gi}Gi LHv2 Volume
    [Arguments]    ${vm_name}
    # TODO: See if there is a better way use suite variables in keywords without passing them as arguments
    &{extra_disk}=    Create Dictionary
    ...    name=${VOL_NAME}
    ...    size=${size_gi}Gi
    ...    storage_class=${SC_NAME}
    @{extra_disks}=    Create List    ${extra_disk}
    virtualmachine.VM is created    ${vm_name}    ${IMAGE_NAME}    extra_disks=${extra_disks}
