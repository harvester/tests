*** Settings ***
Documentation    VM Keywords
Library          Collections
Resource         variables.resource
Resource         common.resource
Resource         volume.resource
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

Get VM Volumes
    [Documentation]    Return PVC claim names in VM volume order, skipping non-PVC volumes.
    [Arguments]    ${vm_name}
    &{res}=    Try Get Vm    ${vm_name}
    Should Be True    ${res.success}    VM ${vm_name} does not exist: ${res.message}

    ${volumes}=    Evaluate    $res['message']['spec']['template']['spec'].get('volumes', [])
    ${claim_names}=    Create List
    FOR    ${volume}    IN    @{volumes}
        IF    'persistentVolumeClaim' in $volume
            Append To List    ${claim_names}    ${volume}[persistentVolumeClaim][claimName]
        END
    END
    RETURN    ${claim_names}

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

VM condition should be
    [Arguments]    ${vm_name}    ${condition}    ${status}    ${match_field}=type
    [Documentation]    Wait until the VM's status.conditions reaches the expected
    ...    state. ${condition} is compared against the condition's `type` by
    ...    default; pass match_field=reason to match reason-only conditions
    ...    (e.g. GuestNotRunning, Unschedulable).
    ${result}=    vm_keywords.wait_for_vm_condition    ${vm_name}    ${condition}    ${status}
    ...    match_field=${match_field}
    RETURN    ${result}

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

VM is soft-rebooted
    [Arguments]    ${vm_name}
    [Documentation]    Soft-reboot a running VM (guest-level reboot via
    ...    qemu-guest-agent), unlike restart which tears down and recreates the VMI
    vm_keywords.softreboot vm    ${vm_name}

VM qemu-agent should be disconnected
    [Arguments]    ${vm_name}    &{config}
    [Documentation]    Wait until the VM's guest agent disconnects (i.e. the
    ...    AgentConnected condition is removed), meaning the guest is
    ...    rebooting/leaving the OS.
    vm_keywords.wait_for_vm_agent_disconnected    ${vm_name}    &{config}

VM qemu-agent should be connected
    [Arguments]    ${vm_name}    &{config}
    [Documentation]    Wait until the VM's guest agent connects (i.e. the
    ...    AgentConnected condition appears). Right after VM creation/start
    ...    only Ready/LiveMigratable/StorageLiveMigratable exist yet, so this
    ...    must be polled rather than checked once. Returns the condition
    ...    dict, which includes `lastProbeTime`.
    ${condition}=    vm_keywords.wait_for_vm_agent_connected    ${vm_name}    &{config}
    RETURN    ${condition}

Agent probe time should be updated
    [Arguments]    ${old_probe_time}    ${new_probe_time}
    [Documentation]    Assert the guest agent's lastProbeTime advanced,
    ...    confirming the agent actually reconnected after a soft-reboot
    ...    rather than never having disconnected.
    vm_keywords.verify_agent_probe_time_updated    ${old_probe_time}    ${new_probe_time}

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

VM does not exist
    [Arguments]    ${vm_name}
    [Documentation]    Assert a VM does not exist (is not found)
    ${result}=    Try To Get VM    ${vm_name}
    Operation Should Be Not Found    ${result}

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

Get VM node
    [Arguments]    ${vm_name}
    [Documentation]    Return the node currently running the VM (the VMI's
    ...    status.nodeName), or None when the VM is not running.
    ${node}=    vm_keywords.get_vm_node    ${vm_name}
    RETURN    ${node}

VM should be running on node
    [Arguments]    ${vm_name}    ${expected_node}
    [Documentation]    Assert the VM is currently running on ${expected_node}
    vm_keywords.verify_vm_on_node    ${vm_name}    ${expected_node}

VM should be moved off node
    [Arguments]    ${vm_name}    ${original_node}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the VM is Running on any node other than
    ...    ${original_node}, without requesting a specific destination. Used when
    ...    something else (e.g. the descheduler) decides where the VM lands.
    ...    Returns the node the VM ended up on.
    ${node}=    vm_keywords.wait_for_vm_migrated_away_from    ${vm_name}    ${original_node}
    ...    timeout=${timeout}
    RETURN    ${node}

Get VM annotations
    [Arguments]    ${vm_name}
    [Documentation]    Return the VM object's metadata.annotations as a dictionary
    ${annotations}=    vm_keywords.get_vm_annotations    ${vm_name}
    RETURN    ${annotations}

VM annotation should be
    [Arguments]    ${vm_name}    ${key}    ${value}
    [Documentation]    Assert the VM carries an annotation with the expected value.
    ...    Controllers set annotations asynchronously, so this polls.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM Annotation Value Is    ${vm_name}    ${key}    ${value}

VM Annotation Value Is
    [Arguments]    ${vm_name}    ${key}    ${value}
    [Documentation]    Single-shot assertion backing `VM annotation should be`
    ${annotations}=    Get VM annotations    ${vm_name}
    Dictionary Should Contain Item    ${annotations}    ${key}    ${value}
    ...    msg=VM ${vm_name} annotation ${key} should be '${value}'

VM annotation should be absent
    [Arguments]    ${vm_name}    ${key}
    [Documentation]    Assert the VM does not carry the given annotation.
    ...    Controllers remove annotations asynchronously, so this polls.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM Annotation Is Not Present    ${vm_name}    ${key}

VM Annotation Is Not Present
    [Arguments]    ${vm_name}    ${key}
    [Documentation]    Single-shot assertion backing `VM annotation should be absent`
    ${annotations}=    Get VM annotations    ${vm_name}
    Dictionary Should Not Contain Key    ${annotations}    ${key}
    ...    msg=VM ${vm_name} should not carry annotation ${key}

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

Execute Command In VM
    [Arguments]    ${vm_name}    ${command}    ${username}    ${pkey}=${None}
    [Documentation]    Execute a command inside the VM's guest OS over SSH,
    ...    using the Harvester host node running the VM as a jump host
    ...    (see SSH_PRIVATE_KEY in variables.resource).
    ...    Returns the combined stdout and stderr as a single value.
    ${output}=    vm_keywords.exec_command_in_vm    ${vm_name}    ${command}
    ...    ${username}    pkey=${pkey}
    RETURN    ${output}

VM cloud-init should be done
    [Arguments]    ${vm_name}    ${username}    ${pkey}=${None}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Poll `cloud-init status` inside the VM guest over SSH
    ...    until it reports done.
    vm_keywords.wait_for_vm_cloudinit_done    ${vm_name}    ${username}
    ...    pkey=${pkey}    timeout=${timeout}

Get VM CPU Cores
    [Arguments]    ${vm_name}
    [Documentation]    Get the VM spec's requested CPU core count
    ${cores}=    vm_keywords.get_vm_cpu_cores    ${vm_name}
    RETURN    ${cores}

VM CPU is updated to ${cpu_cores}
    [Arguments]    ${vm_name}
    [Documentation]    Update the VM's CPU core count
    vm_keywords.update_vm_cpu_cores    ${vm_name}    ${cpu_cores}


VM Disk Performance Should Be
    [Arguments]    ${vm_name}    ${disk_name}    ${from_vmi}=${False}    &{expected}
    [Documentation]    Assert a disk's KubeVirt performance fields (cache, io,
    ...    dedicatedIOThread) in the VM spec, or in the running VMI when
    ...    from_vmi=${True}. Only the fields passed in &{expected} are compared.
    ${actual}=    vm_keywords.get_vm_disk_performance    ${vm_name}    ${disk_name}
    ...    from_vmi=${from_vmi}
    FOR    ${field}    ${value}    IN    &{expected}
        Dictionary Should Contain Key    ${actual}    ${field}
        ...    msg=Disk ${disk_name} of VM ${vm_name} has no ${field}: ${actual}
        Should Be Equal As Strings    ${actual}[${field}]    ${value}    ignore_case=True
        ...    msg=Disk ${disk_name} of VM ${vm_name}: ${field} is ${actual}[${field}], expected ${value}
    END

VM Domain IO Settings Should Be
    [Arguments]    ${vm_name}    ${from_vmi}=${False}    &{expected}
    [Documentation]    Assert the VM-wide storage settings (blockMultiQueue,
    ...    ioThreadsPolicy, supplementalPoolThreadCount) in the VM spec, or in
    ...    the running VMI when from_vmi=${True}. Only the settings passed in
    ...    &{expected} are compared.
    ${actual}=    vm_keywords.get_vm_domain_io_settings    ${vm_name}    from_vmi=${from_vmi}
    FOR    ${setting}    ${value}    IN    &{expected}
        Dictionary Should Contain Key    ${actual}    ${setting}
        ...    msg=VM ${vm_name} has no ${setting}: ${actual}
        Should Be Equal As Strings    ${actual}[${setting}]    ${value}    ignore_case=True
        ...    msg=VM ${vm_name}: ${setting} is ${actual}[${setting}], expected ${value}
    END

VM Launched Disk Driver Should Be
    [Arguments]    ${vm_name}    ${disk_name}    &{expected}
    [Documentation]    Assert attributes of a disk's libvirt <driver> element
    ...    (e.g. cache, io, queues) in the domain the VM's virt-launcher
    ...    started, which is what QEMU actually runs with.
    ${actual}=    vm_keywords.get_vm_launched_disk_driver    ${vm_name}    ${disk_name}
    FOR    ${attribute}    ${value}    IN    &{expected}
        Dictionary Should Contain Key    ${actual}    ${attribute}
        ...    msg=Disk ${disk_name} of VM ${vm_name} has no ${attribute} in its domain: ${actual}
        Should Be Equal As Strings    ${actual}[${attribute}]    ${value}
        ...    msg=Disk ${disk_name} of VM ${vm_name}: domain ${attribute} is ${actual}[${attribute}], expected ${value}
    END

VM Should Boot And Write To Disk
    [Arguments]    ${vm_name}    ${username}    ${pkey}=${None}
    [Documentation]    Wait for the guest to boot, then write and read back data
    ...    with O_DIRECT so the I/O goes through the configured disk path.
    VM should be running    ${vm_name}
    VM should have IP addresses    ${vm_name}
    VM cloud-init should be done    ${vm_name}    ${username}    pkey=${pkey}
    ${output}=    Execute Command In VM    ${vm_name}
    ...    sudo dd if=/dev/urandom of=/var/tmp/perf-check bs=1M count=16 oflag=direct status=none && sudo sha256sum /var/tmp/perf-check | cut -c1-8
    ...    ${username}    pkey=${pkey}
    Should Match Regexp    ${output.strip()}    ^[0-9a-f]{8}$
    ...    msg=Failed to write to the disk of ${vm_name}: ${output}

# VM network (NAD) changes, KubeVirt LiveUpdateNADRef (harvester/harvester#11769)
VM is created with bridge NIC
    [Arguments]    ${vm_name}    ${image_id}    ${network}    ${mac_address}    ${nic_name}=nic-1
    ...    ${cpu}=1    ${memory}=2Gi    &{config}
    [Documentation]    Create a VM whose only NIC is a bridge interface on the
    ...    VM network (NAD) ${network}, with a fixed MAC address. The guest
    ...    gets cloud-init networkData with DHCP off on that NIC. Extra
    ...    &{config} is passed to `VM is created` (e.g. disk_size,
    ...    run_strategy, boot_disk_access_mode, requests_memory).
    ${nic}=    Create Dictionary    name=${nic_name}    network=${network}    mac_address=${mac_address}
    @{interfaces}=    Create List    ${nic}
    VM is created    ${vm_name}    ${image_id}    ${cpu}    ${memory}
    ...    interfaces=${interfaces}    management_network=${False}    &{config}

Try To Change VM Network
    [Arguments]    ${vm_name}    ${nic_name}    ${network}
    [Documentation]    Change only spec.template.spec.networks[${nic_name}].multus.networkName
    ...    of the VM, leaving the interface (binding, MAC, model) untouched.
    ...    Returns a {success, code, message} dict; never fails on rejection.
    ${result}=    vm_keywords.try_update_vm_network    ${vm_name}    ${nic_name}    ${network}
    RETURN    ${result}

VM network is changed
    [Arguments]    ${vm_name}    ${nic_name}    ${network}
    [Documentation]    Change only the NAD of a VM network; the update must be accepted
    ${result}=    Try To Change VM Network    ${vm_name}    ${nic_name}    ${network}
    Should Be True    ${result}[success]
    ...    msg=Changing ${nic_name} of VM ${vm_name} to ${network} was rejected (code=${result}[code]): ${result}[message]

VM Update Should Be Rejected
    [Arguments]    ${result}    @{expected_messages}
    [Documentation]    Assert a {success, code, message} VM update result was
    ...    rejected. The Harvester VM webhook reports its denials as
    ...    InternalError (500), so any error code is accepted; the message
    ...    must contain at least one of expected_messages (case-insensitive)
    ...    when given.
    Should Not Be True    ${result}[success]
    ...    msg=VM update was expected to be rejected but succeeded
    IF    ${expected_messages}
        ${msg_lower}=    Convert To Lower Case    ${result}[message]
        ${lowered}=    Evaluate    [m.lower() for m in $expected_messages]
        Should Contain Any    ${msg_lower}    @{lowered}
        ...    msg=Expected message to contain one of ${expected_messages}, got: ${result}[message]
    END

VM condition reason should be
    [Arguments]    ${vm_name}    ${condition}    ${status}    ${reason}    ${from_vmi}=${False}
    [Documentation]    Wait until the VM (or its VMI with from_vmi=${True})
    ...    has condition ${condition} with the given status and reason.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM Condition Is    ${vm_name}    ${condition}    ${status}    ${reason}    ${from_vmi}

VM Condition Is
    [Arguments]    ${vm_name}    ${condition}    ${status}    ${reason}    ${from_vmi}=${False}
    [Documentation]    Single-shot assertion backing `VM condition reason should be`
    ${conditions}=    vm_keywords.get_vm_conditions    ${vm_name}    from_vmi=${from_vmi}
    ${matches}=    Evaluate    [c for c in $conditions if (c.get('type'), c.get('status'), c.get('reason', '')) == ($condition, $status, $reason)]
    Should Not Be Empty    ${matches}
    ...    msg=${vm_name} has no condition ${condition}=${status} (${reason}): ${conditions}

VM should not have condition
    [Arguments]    ${vm_name}    ${condition}    ${from_vmi}=${False}
    [Documentation]    Assert the VM (or its VMI with from_vmi=${True}) does
    ...    not carry condition ${condition} with status True.
    ${conditions}=    vm_keywords.get_vm_conditions    ${vm_name}    from_vmi=${from_vmi}
    ${matches}=    Evaluate    [c for c in $conditions if c.get('type') == $condition and c.get('status') == 'True']
    Should Be Empty    ${matches}
    ...    msg=${vm_name} unexpectedly has condition ${condition}: ${matches}

Get VM migrations
    [Arguments]    ${vm_name}
    [Documentation]    Return the names of the VM's VirtualMachineInstanceMigrations
    ${names}=    vm_keywords.list_vm_migration_names    ${vm_name}
    RETURN    ${names}

VM workload update migration should be created
    [Arguments]    ${vm_name}    ${known_migrations}
    [Documentation]    Wait for a migration created by KubeVirt's workload
    ...    updater (kubevirt-workload-update-*) that is not in
    ...    ${known_migrations}. Returns its name.
    ${name}=    vm_keywords.wait_for_new_vm_migration    ${vm_name}    ${known_migrations}
    ...    name_prefix=kubevirt-workload-update-    timeout=${WAIT_TIMEOUT}
    RETURN    ${name}

VM migration should succeed
    [Arguments]    ${migration_name}
    [Documentation]    Wait until the VirtualMachineInstanceMigration Succeeds
    vm_keywords.wait_for_vm_migration_phase    ${migration_name}    Succeeded    timeout=${WAIT_TIMEOUT}

VM should not be migrated
    [Arguments]    ${vm_name}    ${known_migrations}    ${duration}=60
    [Documentation]    Assert no migration of the VM besides ${known_migrations}
    ...    appears within ${duration} seconds.
    vm_keywords.wait_for_no_new_vm_migration    ${vm_name}    ${known_migrations}    ${duration}

VMI network should be
    [Arguments]    ${vm_name}    ${nic_name}    ${network}
    [Documentation]    Wait until the running VMI's spec.networks maps
    ...    ${nic_name} to the VM network ${network}.
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VMI Network Is    ${vm_name}    ${nic_name}    ${network}

VMI Network Is
    [Arguments]    ${vm_name}    ${nic_name}    ${network}
    [Documentation]    Single-shot assertion backing `VMI network should be`
    ${networks}=    vm_keywords.get_vmi_networks    ${vm_name}
    Dictionary Should Contain Item    ${networks}    ${nic_name}    ${network}
    ...    msg=VMI ${vm_name} network ${nic_name} should be ${network}: ${networks}

Get VMI interface MAC
    [Arguments]    ${vm_name}    ${nic_name}
    [Documentation]    Return the MAC address the running VMI reports for ${nic_name}
    ${macs}=    vm_keywords.get_vmi_interface_macs    ${vm_name}
    Dictionary Should Contain Key    ${macs}    ${nic_name}
    ...    msg=VMI ${vm_name} reports no interface ${nic_name}: ${macs}
    RETURN    ${macs}[${nic_name}]

VMI interface MAC should be
    [Arguments]    ${vm_name}    ${nic_name}    ${mac_address}
    [Documentation]    Assert the running VMI reports ${mac_address} for ${nic_name}
    ${mac}=    Get VMI interface MAC    ${vm_name}    ${nic_name}
    Should Be Equal As Strings    ${mac}    ${mac_address}    ignore_case=True
    ...    msg=VMI ${vm_name} ${nic_name} MAC is ${mac}, expected ${mac_address}

VM launcher pod should be attached to network
    [Arguments]    ${vm_name}    ${network}    ${mac_address}
    [Documentation]    Assert the Multus network-status of the virt-launcher
    ...    pod the VMI runs in lists ${network} with ${mac_address}.
    ${status}=    vm_keywords.get_vm_launcher_network_status    ${vm_name}
    ${matches}=    Evaluate    [n for n in $status if (n.get('name'), n.get('mac', '').lower()) == ($network, $mac_address.lower())]
    Should Not Be Empty    ${matches}
    ...    msg=virt-launcher pod of ${vm_name} is not attached to ${network} with MAC ${mac_address}: ${status}

VM launcher pod should not be attached to network
    [Arguments]    ${vm_name}    ${network}
    [Documentation]    Assert the Multus network-status of the virt-launcher
    ...    pod the VMI runs in does not list ${network}.
    ${status}=    vm_keywords.get_vm_launcher_network_status    ${vm_name}
    ${matches}=    Evaluate    [n for n in $status if n.get('name') == $network]
    Should Be Empty    ${matches}
    ...    msg=virt-launcher pod of ${vm_name} is still attached to ${network}: ${status}
