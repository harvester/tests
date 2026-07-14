*** Settings ***
Documentation    VM Keywords
Resource         variables.resource
Resource         common.resource
Library          ../libs/keywords/vm_keywords.py

*** Keywords ***
List VMs by prefix
    [Arguments]    ${prefix}    ${namespace}=default
    [Documentation]    List VMs whose names start with the given prefix
    ${vms}=    vm_keywords.list vms    namespace=${namespace}    name_prefix=${prefix}
    RETURN    ${vms}

VM is created
    [Arguments]    ${vm_name}    ${image_id}    ${cpu}=2    ${memory}=4Gi    &{config}
    [Documentation]    Create a virtual machine with provided name
    vm_keywords.create vm    ${vm_name}    ${image_id}    ${cpu}    ${memory}    &{config}

VM is deleted
    [Arguments]    ${vm_name}
    [Documentation]    Delete a VM
    vm_keywords.delete vm    ${vm_name}

Stopped VM is created
    [Arguments]    ${vm_name}    ${image_id}    ${cpu}=2    ${memory}=4Gi
    [Documentation]    Create a VM that does not boot (runStrategy=Halted)
    vm_keywords.create vm    ${vm_name}    ${image_id}    ${cpu}    ${memory}    run_strategy=Halted

VM is created with extra disks
    [Arguments]    ${vm_name}    ${image_id}    @{sizes}
    [Documentation]    Create a VM with additional blank data disks of the given sizes
    @{disks}=    Create List
    FOR    ${size}    IN    @{sizes}
        ${disk}=    Create Dictionary    size=${size}
        Append To List    ${disks}    ${disk}
    END
    vm_keywords.create vm    ${vm_name}    ${image_id}    2    4Gi    extra_disks=${disks}

VM is created with existing volume
    [Arguments]    ${vm_name}    ${image_id}    ${pvc_name}
    [Documentation]    Create a VM that attaches an already-existing PVC as a data disk
    @{existing}=    Create List    ${pvc_name}
    vm_keywords.create vm    ${vm_name}    ${image_id}    2    4Gi    existing_volumes=${existing}

VM Disk Count Should Be
    [Arguments]    ${vm_name}    ${expected}
    [Documentation]    Assert the VM declares the expected number of disks
    ${names}=    vm_keywords.get_vm_disk_names    ${vm_name}
    Length Should Be    ${names}    ${expected}

Add Volume To VM
    [Arguments]    ${vm_name}    ${disk_name}    ${volume_name}
    [Documentation]    Hot-plug an existing volume into a running VM
    vm_keywords.add_volume_to_vm    ${vm_name}    ${disk_name}    ${volume_name}

Remove Volume From VM
    [Arguments]    ${vm_name}    ${disk_name}
    [Documentation]    Hot-unplug a disk from a running VM
    vm_keywords.remove_volume_from_vm    ${vm_name}    ${disk_name}

Volume Should Be Hotplugged
    [Arguments]    ${vm_name}    ${disk_name}
    [Documentation]    Wait until the hot-plugged disk is Ready in the VMI volumeStatus
    vm_keywords.wait_for_vm_volume_hotplugged    ${vm_name}    ${disk_name}

Volume Should Be Unplugged
    [Arguments]    ${vm_name}    ${disk_name}
    [Documentation]    Wait until the disk is gone from the VMI volumeStatus
    vm_keywords.wait_for_vm_volume_unplugged    ${vm_name}    ${disk_name}

VM is started
    [Arguments]    ${vm_name}
    [Documentation]    Start a VM
    vm_keywords.start vm    ${vm_name}

VM is restarted
    [Arguments]    ${vm_name}
    [Documentation]    Restart a VM (stop then start)
    vm_keywords.restart vm    ${vm_name}

VM is paused
    [Arguments]    ${vm_name}
    [Documentation]    Pause a running VM
    vm_keywords.pause vm    ${vm_name}

VM is unpaused
    [Arguments]    ${vm_name}
    [Documentation]    Unpause a paused VM
    vm_keywords.unpause vm    ${vm_name}

VM should be paused
    [Arguments]    ${vm_name}
    [Documentation]    Wait for VM to reach the paused state
    vm_keywords.wait for vm paused    ${vm_name}

Try To Get VM
    [Arguments]    ${vm_name}
    [Documentation]    Attempt to get a VM expected to be missing. Returns result dict.
    ${result}=    vm_keywords.try_get_vm    ${vm_name}
    RETURN    ${result}

Try To Delete VM
    [Arguments]    ${vm_name}
    [Documentation]    Attempt to delete a VM expected to be missing. Returns result dict.
    ${result}=    vm_keywords.try_delete_vm    ${vm_name}
    RETURN    ${result}

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
    [Arguments]    ${vm_name}    ${networks}=${None}
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

Update Volume Size to ${new_size}Gi From VM
    [Arguments]    ${vm_name}    ${disk_name}
    [Documentation]    Update the size of a VM disk
    vm_keywords.update_vm_disk_size    ${vm_name}    ${disk_name}    ${new_size}Gi
