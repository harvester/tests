*** Settings ***
Documentation    Clean up the shared volume group and disable the LVM addon.
Test Tags        regression    addon    lvm

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/lvm_driver.resource


*** Test Cases ***
Cleanup Volume Group And Disable LVM Addon
    [Tags]    p0    lvm-teardown
    # All stage-2 suites have finished and deleted their volumes and
    # snapshots; any provisioner helper pod still around is a driver leak.
    No LVM Helper Pods Should Remain
    Cleanup LVM Test Environment
