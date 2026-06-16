*** Settings ***
Documentation    VM Keywords
Resource         variables.resource
Resource         common.resource
Resource         image.resource
Library          ../libs/keywords/vm_keywords.py
Library          ../libs/keywords/snapshot_keywords.py
Library          Collections

*** Variables ***
@{VMS_CREATED}
@{VMS_RESTORED}
&{VM_CHECKSUMS}              &{EMPTY}
&{VM_SNAPSHOTS}              &{EMPTY}

*** Keywords ***
List VMs by prefix
    [Arguments]    ${prefix}    ${namespace}=default
    [Documentation]    List VMs whose names start with the given prefix
    ${vms}=    vm_keywords.list vms    namespace=${namespace}    name_prefix=${prefix}
    RETURN    ${vms}

VM is created
    [Arguments]    ${vm_name}    &{config}
    [Documentation]    Create a virtual machine with provided name
    vm_keywords.create vm    ${vm_name}    &{config}

VM is deleted
    [Arguments]    ${vm_name}
    [Documentation]    Delete a VM
    vm_keywords.delete vm    ${vm_name}

VM is started
    [Arguments]    ${vm_name}
    [Documentation]    Start a VM
    vm_keywords.start vm    ${vm_name}

VM is stopped
    [Arguments]    ${vm_name}
    [Documentation]    Stop a VM
    vm_keywords.stop vm    ${vm_name}

VM should be running
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to reach running state
    vm_keywords.wait for vm running    ${vm_name}

VM should be stopped
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to stop
    vm_keywords.wait for vm stopped    ${vm_name}

VM should be deleted
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to be deleted
    vm_keywords.wait for vm deleted    ${vm_name}

VM should have IP addresses
    [Arguments]    ${vm_name}    ${networks}
    [Documentation]    Wait for VM to obtain IP addresses
    vm_keywords.wait for vm ip addresses    ${vm_name}    ${networks}

Data is written to VM
    [Arguments]    ${vm_name}    ${data_size_mb}=100
    [Documentation]    Write data to VM and return checksum
    ${checksum}=    vm_keywords.write vm data    ${vm_name}    ${data_size_mb}
    RETURN    ${checksum}

Get VM data checksum
    [Arguments]    ${vm_name}
    [Documentation]    Get checksum of data in VM
    ${checksum}=    vm_keywords.get vm data checksum    ${vm_name}
    RETURN    ${checksum}

Image is available for VM creation
    [Arguments]    ${image_name}    ${image_url}
    [Documentation]    Create an image from URL (delegates to Image module).
    image.Create image from url with name    ${image_name}    ${image_url}
    image.Wait for image downloaded by name    ${image_name}

VM Is Created And Running
    [Arguments]    ${vm_name}    ${image_name}    ${sc_name}=${EMPTY}    ${network_name}=${VLAN_NETWORK_NAME}
    [Documentation]    Create a VM from the given image and wait for it to be running.
    Log    Creating VM ${vm_name} with image ${image_name}
    VM is created    ${vm_name}    image_id=${image_name}    sc_name=${sc_name}    network_name=${network_name}
    VM should be running    ${vm_name}
    Append To List    ${VMS_CREATED}    ${vm_name}
    Set Suite Variable    @{VMS_CREATED}
    Log    VM ${vm_name} is running

VM Is Created with Additional Volume using SC
    [Arguments]    ${vm_name}    ${sc_name}    ${image_name}    ${network_name}=${VLAN_NETWORK_NAME}
    [Documentation]    Create a VM with the given image as root disk and an additional data volume from the StorageClass
    Log    Creating VM ${vm_name} with image ${image_name} and extra data volume from SC ${sc_name}
    vm_keywords.create_vm_with_volume_using_sc    ${vm_name}    ${sc_name}    ${image_name}    network_name=${network_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM State Is Running    ${vm_name}
    Append To List    ${VMS_CREATED}    ${vm_name}
    Set Suite Variable    @{VMS_CREATED}
    Log    VM ${vm_name} created with SC ${sc_name} and running

Volume Is Attached To VM
    [Arguments]    ${vm_name}    ${vol_name}
    [Documentation]    Attach an LVM volume to a running VM
    Log    Attaching volume ${vol_name} to VM ${vm_name}
    vm_keywords.attach_volume_to_vm    ${vm_name}    ${vol_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM State Is Running    ${vm_name}
    Log    Volume ${vol_name} attached to VM ${vm_name}

Get Block Device In VM
    [Arguments]    ${vm_name}    ${expected_disk_size}=${None}
    [Documentation]    Discover the data block device inside the VM and return its path.
    ...               When expected_disk_size is provided (e.g. 5Gi) the check also
    ...               filters by disk size to avoid matching the wrong device.
    ...               Returns the device path (e.g. /dev/vdb) for use in subsequent steps.
    Log    Getting block device in VM ${vm_name}
    ${device}=    vm_keywords.check_block_device_in_vm    ${vm_name}    ${expected_disk_size}
    Log    Block device ${device} found in VM ${vm_name}
    RETURN    ${device}

VM State Is Running
    [Arguments]    ${vm_name}
    [Documentation]    Assert that VM is in running state
    ${is_running}=    vm_keywords.is_vm_running    ${vm_name}
    Should Be True    ${is_running}    VM ${vm_name} is not running

VM State Is Stopped
    [Arguments]    ${vm_name}
    [Documentation]    Assert that VM is in stopped state
    ${is_stopped}=    vm_keywords.is_vm_stopped    ${vm_name}
    Should Be True    ${is_stopped}    VM ${vm_name} is not stopped

# LVM VM Power Operations
VM Is Powered Off
    [Arguments]    ${vm_name}
    [Documentation]    Stop the VM
    Log    Stopping LVM VM ${vm_name}
    vm_keywords.stop_vm    ${vm_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM State Is Stopped    ${vm_name}
    Log    LVM VM ${vm_name} stopped

VM Is Powered On And Running
    [Arguments]    ${vm_name}
    [Documentation]    Start VM and wait for running
    Log    Starting LVM VM ${vm_name}
    vm_keywords.start_vm    ${vm_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM State Is Running    ${vm_name}
    Log    LVM VM ${vm_name} started and running

# LVM Data Operations Keywords
Data Is Written To Disk And Checksum Recorded
    [Arguments]    ${vm_name}    ${device}    ${format_device}=${True}
    [Documentation]    Mount device, write data and record md5sum.
    ...               Set format_device=${False} for Filesystem volumes (pre-formatted by CSI).
    ...               Set format_device=${True} (default) for Block volumes (mkfs.ext4 first).
    Log    Writing data to ${device} on VM ${vm_name}
    ${checksum}=    vm_keywords.write_data_and_get_checksum_on_disk    ${vm_name}    ${device}    ${format_device}
    Set To Dictionary    ${VM_CHECKSUMS}    ${vm_name}    ${checksum}
    Set Suite Variable    &{VM_CHECKSUMS}
    Log    Data written to VM ${vm_name}, checksum: ${checksum}

Data Is Deleted From Test VMs
    [Documentation]    Delete test data from all running LVM VMs
    Log    Deleting data from LVM VMs
    FOR    ${vm_name}    IN    @{VMS_CREATED}
        ${is_running}=    vm_keywords.is_vm_running    ${vm_name}
        Run Keyword If    ${is_running}    vm_keywords.delete_data_from_vm    ${vm_name}
    END
    Log    Data deleted from all running LVM VMs

# LVM Snapshot Keywords
VM Snapshots Are Taken
    [Documentation]    Take VM snapshots for all running LVM VMs
    Log    Taking snapshots of running LVM VMs
    FOR    ${vm_name}    IN    @{VMS_CREATED}
        ${is_running}=    vm_keywords.is_vm_running    ${vm_name}
        IF    ${is_running}
            ${snapshot_name}=    snapshot_keywords.take_vm_snapshot    ${vm_name}
            Set To Dictionary    ${VM_SNAPSHOTS}    ${vm_name}    ${snapshot_name}
        END
    END
    Set Suite Variable    &{VM_SNAPSHOTS}
    Log    Snapshots taken: ${VM_SNAPSHOTS}

Snapshots Are Restored To New VMs
    [Documentation]    Restore snapshots to newly created VMs
    Log    Restoring LVM snapshots to new VMs
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        ${new_vm_name}=    Set Variable    ${vm_name}-restored
        snapshot_keywords.restore_snapshot_to_new_vm    ${snapshot_name}    ${new_vm_name}
        Append To List    ${VMS_RESTORED}    ${new_vm_name}
        Set Suite Variable    @{VMS_RESTORED}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    VM State Is Running    ${new_vm_name}
    END
    Log    All snapshots restored to new VMs

Restored VMs Have Correct Data
    [Documentation]    Verify restored VMs contain original data
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        ${new_vm_name}=    Set Variable    ${vm_name}-restored
        ${expected_checksum}=    Get From Dictionary    ${VM_CHECKSUMS}    ${vm_name}
        vm_keywords.mount_data_disk_in_vm    ${new_vm_name}
        ${actual_checksum}=    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    vm_keywords.get_data_checksum_from_vm    ${new_vm_name}
        Should Be Equal    ${actual_checksum}    ${expected_checksum}
        ...    Data mismatch on restored VM ${new_vm_name}
    END
    Log    All restored VMs verified

Snapshots Are Restored To Existing VMs
    [Documentation]    Restore snapshots back to existing VMs
    ...    All VMs are stopped first before any restore is initiated.
    Log    Stopping all VMs before restore
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        vm_keywords.stop_vm    ${vm_name}
    END
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    VM State Is Stopped    ${vm_name}
    END
    Log    All VMs stopped, restoring snapshots
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        snapshot_keywords.restore_snapshot_to_existing_vm    ${snapshot_name}    ${vm_name}
    END
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
        ...    VM State Is Running    ${vm_name}
    END
    Log    All snapshots restored to existing VMs

VMs Have Original Data After Restore
    [Documentation]    Verify VMs have original data after snapshot restore
    FOR    ${vm_name}    ${snapshot_name}    IN    &{VM_SNAPSHOTS}
        ${expected_checksum}=    Get From Dictionary    ${VM_CHECKSUMS}    ${vm_name}
        vm_keywords.mount_data_disk_in_vm    ${vm_name}
        ${actual_checksum}=    vm_keywords.get_data_checksum_from_vm    ${vm_name}
        Should Be Equal    ${actual_checksum}    ${expected_checksum}
        ...    Data mismatch on VM ${vm_name} after restore
    END
    Log    All VMs have correct data after restore

# LVM Volume Expand Via VM Keywords
Volume Is Expanded Via VM Edit
    [Arguments]    ${vm_name}    ${vol_name}    ${new_size}
    [Documentation]    Expand LVM volume by editing the VM spec
    Log    Expanding volume ${vol_name} on VM ${vm_name} to ${new_size} via VM edit
    vm_keywords.expand_volume_via_vm_edit    ${vm_name}    ${vol_name}    ${new_size}
    Log    Volume ${vol_name} expanded to ${new_size} via VM edit

Volume Size Inside VM Is Correct
    [Arguments]    ${vm_name}    ${expected_size}
    [Documentation]    Verify the volume size inside the VM matches expected
    Log    Verifying volume size inside VM ${vm_name} is ${expected_size}
    ${actual_size}=    vm_keywords.get_volume_size_inside_vm    ${vm_name}    ${expected_size}
    Should Be True    ${actual_size}
    ...    Volume size inside VM ${vm_name} does not match expected ${expected_size}
    Log    Volume size inside VM ${vm_name} is correct: ${expected_size}
