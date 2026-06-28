*** Settings ***
Documentation    VM Volume Hot-Plug / Hot-Unplug Test Cases
...    Port of harvester/tests test_3_vm_functions.py TestHotPlugVolume.
...    Verified via the VMI status.volumeStatus (CRD-only, no in-guest check).
Test Tags        virtualmachines    volumes    pr-baseline

Resource    ../../keywords/variables.resource
Resource    ../../keywords/common.resource
Resource    ../../keywords/image.resource
Resource    ../../keywords/volume.resource
Resource    ../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${HP_DISK}     disk-hot-plug
# Dynamic Variables
${IMG_NAME}    ${EMPTY}
${VM_NAME}     ${EMPTY}
${DATA_VOL}    ${EMPTY}


*** Test Cases ***
Hot-Plug Volume Into Running VM
    [Tags]    p0    smoke
    [Documentation]    Hot-plug an existing volume into a running VM; it must
    ...    appear Ready in the VMI volumeStatus.
    Add Volume To VM    ${VM_NAME}    ${HP_DISK}    ${DATA_VOL}
    Volume Should Be Hotplugged    ${VM_NAME}    ${HP_DISK}

Hot-Unplug Volume From Running VM
    [Tags]    p0    smoke
    [Documentation]    Hot-unplug the disk; it must disappear from the VMI volumeStatus.
    Remove Volume From VM    ${VM_NAME}    ${HP_DISK}
    Volume Should Be Unplugged    ${VM_NAME}    ${HP_DISK}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set Suite Variable    ${VM_NAME}     vm-${suffix}
    Set Suite Variable    ${DATA_VOL}    vol-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    VM is created    ${VM_NAME}    ${IMG_NAME}
    VM should be running    ${VM_NAME}
    Create Volume    ${DATA_VOL}    1Gi
    Wait Until Volume Is Active    ${DATA_VOL}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${DATA_VOL}
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
