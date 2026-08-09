*** Settings ***
Documentation    Prepare the LVM addon and shared volume group for parallel LVM suites.
Test Tags        regression    addon    lvm

Resource         ../../../../keywords/lvm.resource


*** Test Cases ***
Enable LVM Addon And Provision Volume Group
    [Tags]    p0    smoke    lvm-setup
    Prepare LVM Test Environment
