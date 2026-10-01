*** Settings ***
Documentation    Shared keywords and variables for parallel LVM addon suites.

Resource         addon.resource
Resource         common.resource
Resource         image.resource
Resource         storage.resource
Resource         storageclass.resource
Resource         virtualmachine.resource
Resource         volume.resource
Resource         lvm_driver.resource


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
    # An interrupted run leaves its volume group behind. Reuse it: the addon
    # manifest ships disabled and cannot be applied again while LVM resources
    # exist, and the disk is no longer unprovisioned.
    ${node}=    Find LVM Volume Group Node    ${LVM_TEST_RUN_ID}    ${LVM_VG_NAME}
    IF    $node is None
        Provision LVM Volume Group
    ELSE
        Log    Reusing volume group ${LVM_VG_NAME} on ${node}    console=yes
        Wait For Enabled    ${LVM_ADDON_NAME}
    END
    # VM snapshots of LVM-backed volumes are only admitted when the driver
    # has a snapshot class registered in the csi-driver-config setting.
    Configure LVM Snapshot Class In CSI Driver Config

Provision LVM Volume Group
    Install Experimental Addon    ${LVM_ADDON_NAME}    ${LVM_ADDON_URL}
    Enable    ${LVM_ADDON_NAME}
    Wait For Enabled    ${LVM_ADDON_NAME}
    ${disk_by_node}=    Get LVM Suitable Disks    ${LVM_DISK_SIZE}
    # Persist ownership on the BlockDevices. Under Pabot the workload suites
    # and the teardown run in other processes and therefore cannot read suite
    # variables set here.
    Label LVM Test Disks    ${disk_by_node}    ${LVM_TEST_RUN_ID}
    Create LVM Volume Groups    ${disk_by_node}    ${LVM_VG_TYPE}

Teardown LVM Test Environment
    Set up test environment
    # Every workload suite has finished and deleted its volumes and
    # snapshots; any provisioner helper pod still around is a driver leak.
    Run Keyword And Continue On Failure    No LVM Helper Pods Should Remain
    Cleanup LVM Test Environment

Cleanup LVM Test Environment
    Set up test environment
    Run Keyword And Continue On Failure    Cleanup Labelled LVM Volume Groups
    Run Keyword And Continue On Failure    Remove LVM Snapshot Class From CSI Driver Config
    Disable    ${LVM_ADDON_NAME}
    Wait For Disabled    ${LVM_ADDON_NAME}

Cleanup Labelled LVM Volume Groups
    # No disk is labelled when preparation failed before selecting one.
    ${disk_by_node}=    Get LVM Test Disks    ${LVM_TEST_RUN_ID}
    Cleanup LVM Volume Groups    ${disk_by_node}

Initialize LVM Workload Suite
    Set up test environment
    ${node}=    Get LVM Volume Group Node    ${LVM_TEST_RUN_ID}    ${LVM_VG_NAME}
    RETURN    ${node}
