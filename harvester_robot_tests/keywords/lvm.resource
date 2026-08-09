*** Settings ***
Documentation    Shared keywords and variables for parallel LVM addon suites.

Resource         addon.resource
Resource         common.resource
Resource         image.resource
Resource         storage.resource
Resource         storageclass.resource
Resource         virtualmachine.resource
Resource         volume.resource


*** Variables ***
${LVM_ADDON_NAME}       harvester-csi-driver-lvm
${LVM_TEST_RUN_ID}      %{LVM_TEST_RUN_ID=lvm-robot}
${LVM_VG_NAME}          vg-dm-thin
${LVM_VG_TYPE}          dm-thin
${LVM_DISK_SIZE}        50
${LVM_VOLUME_SIZE}      5Gi
${LVM_EXPANDED_SIZE}    10Gi


*** Keywords ***
Prepare LVM Test Environment
    Set up test environment
    Install Addon From URL    ${LVM_ADDON_URL}
    Enable    ${LVM_ADDON_NAME}
    Wait For Enabled    ${LVM_ADDON_NAME}
    ${disk_by_node}=    Get LVM Suitable Disks    ${LVM_DISK_SIZE}
    # Persist ownership on the BlockDevices. The cleanup test is a separate
    # Pabot process and therefore cannot read suite variables from this test.
    Label LVM Test Disks    ${disk_by_node}    ${LVM_TEST_RUN_ID}
    Create LVM Volume Groups    ${disk_by_node}    ${LVM_VG_TYPE}

Cleanup LVM Test Environment
    Set up test environment
    Run Keyword And Continue On Failure    Cleanup Labelled LVM Volume Groups
    Disable    ${LVM_ADDON_NAME}
    Wait For Disabled    ${LVM_ADDON_NAME}

Cleanup Labelled LVM Volume Groups
    ${disk_by_node}=    Get LVM Test Disks    ${LVM_TEST_RUN_ID}
    Cleanup LVM Volume Groups    ${disk_by_node}

Initialize LVM Workload Suite
    Set up test environment
    ${node}=    Get LVM Volume Group Node    ${LVM_TEST_RUN_ID}    ${LVM_VG_NAME}
    RETURN    ${node}
