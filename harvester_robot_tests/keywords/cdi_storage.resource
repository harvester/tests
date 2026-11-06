*** Settings ***
Documentation    Optional LVM storage owned by a CDI test suite.
Resource         lvm.resource


*** Variables ***
${CDI_STORAGE_CLASS}      %{CDI_STORAGE_CLASS=}
${CDI_STORAGE_BACKEND}    %{CDI_STORAGE_BACKEND=none}
${CDI_STORAGE_OWNED}      ${FALSE}
${CDI_LVM_ENABLED}        ${FALSE}


*** Keywords ***
Prepare CDI Storage
    IF    $CDI_STORAGE_CLASS != ''
        RETURN
    END
    Should Be Equal    ${CDI_STORAGE_BACKEND}    lvm
    ${disks}=    Get LVM Suitable Disks    ${LVM_DISK_SIZE}
    ${name}=    Generate Unique Name    cdi
    Storage Class Should Not Exist    ${name}
    ${enabled}=    Is Enabled    ${LVM_ADDON_NAME}
    Set Suite Variable    ${CDI_LVM_ENABLED}    ${enabled}
    Set Suite Variable    ${CDI_STORAGE_CLASS}    ${name}
    Set Suite Variable    ${LVM_TEST_RUN_ID}    ${name}
    # Record ownership before setup can fail partway through provisioning.
    Set Suite Variable    ${CDI_STORAGE_OWNED}    ${TRUE}
    Enable CDI LVM
    Label LVM Test Disks    ${disks}    ${LVM_TEST_RUN_ID}
    Create LVM Volume Groups    ${disks}    ${LVM_VG_TYPE}
    ${node}=    Get LVM Volume Group Node    ${LVM_TEST_RUN_ID}    ${LVM_VG_NAME}
    Create LVM Storage Class
    ...    ${CDI_STORAGE_CLASS}    ${LVM_VG_NAME}    ${LVM_VG_TYPE}    ${node}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Storage Profile Clone Strategy Should Be    ${CDI_STORAGE_CLASS}    snapshot

Enable CDI LVM
    ${exists}=    Addon Exists    ${LVM_ADDON_NAME}
    IF    not $exists
        Install Experimental Addon    ${LVM_ADDON_NAME}    ${LVM_ADDON_URL}
    END
    Enable    ${LVM_ADDON_NAME}
    Wait For Enabled    ${LVM_ADDON_NAME}

Cleanup CDI Storage
    IF    not $CDI_STORAGE_OWNED
        RETURN
    END
    # Keep the class and volume group intact if workload cleanup left volumes.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Storage Class Should Be Unused    ${CDI_STORAGE_CLASS}
    Cleanup Labelled LVM Volume Groups
    Delete Storage Class    ${CDI_STORAGE_CLASS}
    Restore CDI LVM

Restore CDI LVM
    IF    $CDI_LVM_ENABLED
        RETURN
    END
    ${exists}=    Addon Exists    ${LVM_ADDON_NAME}
    IF    not $exists
        RETURN
    END
    Disable    ${LVM_ADDON_NAME}
    Wait For Disabled    ${LVM_ADDON_NAME}
