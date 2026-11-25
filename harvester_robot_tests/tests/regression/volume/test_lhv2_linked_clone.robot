*** Settings ***
Documentation    Longhorn V2 linked-clone volumes for VM images.
...              A Longhorn V2 StorageClass with cloneMode=linked-clone makes Harvester's
...              CDI csi-clone of an image's golden PVC a copy-on-write linked clone instead
...              of a full copy. The suite covers creating VMs from such an image, exporting
...              an image into a linked clone (nested linked clone), and deleting an image
...              while VMs that were cloned from it keep running.
...              Requires the Longhorn V2 Data Engine and at least one schedulable Longhorn V2
...              block disk tagged ${LHV2_DISK_TAG} (override with LHV2_DISK_TAG).
...              Issue harvester/harvester#12359
Test Tags        regression    volume    longhorn    lhv2    linked-clone

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource
Resource    ../../../keywords/storageclass.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${LHV2_DISK_TAG}       %{LHV2_DISK_TAG=lhv2}
# Dynamic Variables
${SC_NAME}             ${EMPTY}
${SC_REPLICAS}         1
${IMAGE_NAME}          ${EMPTY}
${EXPORT_IMAGE_NAME}   ${EMPTY}
${VM_NAME}             ${EMPTY}
${NESTED_VM_NAME}      ${EMPTY}


*** Test Cases ***
Create Linked-Clone Storage Class
    [Tags]    p0
    [Documentation]    A Longhorn V2 StorageClass carries cloneMode=linked-clone.
    When Create LHv2 Linked-Clone Storage Class    ${SC_NAME}    ${SC_REPLICAS}    ${LHV2_DISK_TAG}
    Then Storage Class Parameter Should Be    ${SC_NAME}    cloneMode    linked-clone
    And Storage Class Parameter Should Be    ${SC_NAME}    dataEngine    v2

Create Image On Linked-Clone Storage Class
    [Tags]    p0
    [Documentation]    Importing an image into the StorageClass creates a CDI golden image PVC.
    Given Storage Class Is Present    ${SC_NAME}
    When Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}    storage_class=${SC_NAME}
    Then Wait Until Image State Is Active    ${IMAGE_NAME}

Create VM From Linked-Clone Image
    [Tags]    p0
    [Documentation]    The VM root volume is a linked clone of the image's golden PVC, it is
    ...    expanded to the requested size (larger than the image), and the VM boots.
    Given Image Should Exist    ${IMAGE_NAME}
    When VM is created    ${VM_NAME}    ${IMAGE_NAME}    cpu=1    memory=2Gi    disk_size=10Gi
    Then VM should be running    ${VM_NAME}
    And VM should have IP addresses    ${VM_NAME}
    And Volume ${VM_NAME}-disk-0 Should Be A Linked Clone Of ${IMAGE_NAME}
    And Volume size is 10Gi    ${VM_NAME}-disk-0

Linked Clone Shares Data With The Image
    [Tags]    p1
    [Documentation]    A linked clone stores only the data written to it, so a booted VM's root
    ...    volume allocates less than the image volume it was cloned from.
    Given VM should be running    ${VM_NAME}
    Then Volume ${VM_NAME}-disk-0 Should Allocate Less Than ${IMAGE_NAME}

Export Image To Linked-Clone Image
    [Tags]    p1
    [Documentation]    Exporting the image volume to a new image in the linked-clone
    ...    StorageClass creates the new golden PVC as a linked clone, and a VM created from
    ...    the exported image (a nested linked clone) boots.
    Given Image Should Exist    ${IMAGE_NAME}
    When Export Volume To Image    ${IMAGE_NAME}    ${EXPORT_IMAGE_NAME}    ${SC_NAME}    backend=cdi
    Then Wait Until Image State Is Active    ${EXPORT_IMAGE_NAME}
    And Wait Until Volume ${EXPORT_IMAGE_NAME} Is A Linked Clone Of ${IMAGE_NAME}
    When VM is created    ${NESTED_VM_NAME}    ${EXPORT_IMAGE_NAME}    cpu=1    memory=2Gi    disk_size=10Gi
    Then VM should be running    ${NESTED_VM_NAME}
    And VM should have IP addresses    ${NESTED_VM_NAME}
    And Volume ${NESTED_VM_NAME}-disk-0 Should Be A Linked Clone Of ${EXPORT_IMAGE_NAME}

Delete Image While Linked-Clone VM Is Running
    [Tags]    p1
    [Documentation]    An image can be deleted while VMs cloned from it keep running. Longhorn
    ...    keeps the image's source data until the last linked clone is gone, and then
    ...    removes it.
    Given VM should be running    ${NESTED_VM_NAME}
    ${source}=    Get Longhorn Volume Of    ${EXPORT_IMAGE_NAME}
    ${source_volume}=    Set Variable    ${source}[metadata][name]
    When Delete image by name    ${EXPORT_IMAGE_NAME}
    Then Wait for image deleted by name    ${EXPORT_IMAGE_NAME}
    And VM should be running    ${NESTED_VM_NAME}
    And VM should have IP addresses    ${NESTED_VM_NAME}
    When VM is deleted    ${NESTED_VM_NAME}
    Then VM should be deleted    ${NESTED_VM_NAME}
    And Wait Until Longhorn Volume Is Deleted    ${source_volume}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    lc
    Set Suite Variable    ${SC_NAME}              sc-${suffix}
    Set Suite Variable    ${IMAGE_NAME}           img-${suffix}
    Set Suite Variable    ${EXPORT_IMAGE_NAME}    img-export-${suffix}
    Set Suite Variable    ${VM_NAME}              vm-${suffix}
    Set Suite Variable    ${NESTED_VM_NAME}       vm-nested-${suffix}
    Set up test environment

    ${is_enabled}=    Run Keyword And Return Status    setting.LHv2 Data Engine Is Enabled
    Skip If    not ${is_enabled}    Longhorn V2 Data Engine is not enabled
    ${disks}=    Longhorn V2 Disks With Tag    ${LHV2_DISK_TAG}
    Skip If    not ${disks}    No schedulable Longhorn V2 block disk is tagged ${LHV2_DISK_TAG}
    Set Suite Metadata    LHV2_DISKS    ${disks}

Local Suite Teardown
    # Delete the VMs before the images and the StorageClass: a source volume is only
    # removed after the linked clones that use it are gone
    Run Keyword And Ignore Error    VM is deleted    ${NESTED_VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${EXPORT_IMAGE_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Wait for image deleted by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${SC_NAME}
    Common Suite Teardown
