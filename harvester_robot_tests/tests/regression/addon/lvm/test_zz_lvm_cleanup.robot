*** Settings ***
Documentation    Clean up the shared volume group and disable the LVM addon.
Test Tags        regression    addon    lvm

Resource         ../../../../keywords/lvm.resource


*** Test Cases ***
Cleanup Volume Group And Disable LVM Addon
    [Tags]    p0    lvm-teardown
    Cleanup LVM Test Environment
