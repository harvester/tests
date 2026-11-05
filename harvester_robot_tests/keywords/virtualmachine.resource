*** Settings ***
Documentation    VM Keywords
Library          Collections
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

VM is live-migrated
    [Arguments]    ${vm_name}
    [Documentation]    Start a compute live migration of the VM (a
    ...    VirtualMachineInstanceMigration without a volume change). The
    ...    scheduler picks the destination node.
    vm_keywords.migrate_vm    ${vm_name}    ${None}

Start Storage Migration
    [Arguments]    ${vm_name}    ${source_volume}    ${target_volume}
    [Documentation]    Move a VM volume to another (empty, at least as large)
    ...    PVC while the VM keeps running, like the Harvester
    ...    `storageMigration` VM action: set `targetVolume` on the source
    ...    entry of the harvesterhci.io/volumeClaimTemplates annotation.
    vm_keywords.start_vm_storage_migration    ${vm_name}    ${source_volume}    ${target_volume}

Storage Migration Should Complete
    [Arguments]    ${vm_name}    ${source_volume}    ${target_volume}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until the VM runs on the target PVC, KubeVirt has
    ...    cleared the VolumesChange condition and Harvester has rewritten the
    ...    volumeClaimTemplates entry to the target PVC.
    vm_keywords.wait_for_vm_storage_migration_completed    ${vm_name}
    ...    ${source_volume}    ${target_volume}    timeout=${timeout}

Get VM Launcher Pods
    [Arguments]    ${vm_name}
    [Documentation]    Return the VM's virt-launcher pods as dicts with name,
    ...    phase, terminating and claims (the PVCs in the pod's spec.volumes).
    ${pods}=    vm_keywords.get_vm_launcher_pods    ${vm_name}
    RETURN    ${pods}

VM Should Have A Completed Launcher Pod
    [Arguments]    ${vm_name}
    [Documentation]    Assert the VM has a virt-launcher pod in the Succeeded
    ...    phase that is not being deleted (the source pod of a migration).
    ${pods}=    Get VM Launcher Pods    ${vm_name}
    ${completed}=    Evaluate
    ...    [p['name'] for p in $pods if p['phase'] == 'Succeeded' and not p['terminating']]
    Should Not Be Empty    ${completed}
    ...    msg=VM ${vm_name} has no Completed virt-launcher pod: ${pods}

VM Launcher Pods Should Not Use Volume
    [Arguments]    ${vm_name}    ${volume_name}
    [Documentation]    Single-shot assertion: no virt-launcher pod of the VM
    ...    lists the PVC in spec.volumes.
    ${pods}=    Get VM Launcher Pods    ${vm_name}
    ${holders}=    Evaluate
    ...    [f"{p['name']} ({p['phase']})" for p in $pods if $volume_name in p['claims']]
    Should Be Empty    ${holders}
    ...    msg=virt-launcher pods of VM ${vm_name} still use volume ${volume_name}: ${holders}

VM Should Run Only On Volume
    [Arguments]    ${vm_name}    ${volume_name}
    [Documentation]    Assert the VM has exactly one running virt-launcher pod
    ...    and that it uses the given PVC.
    ${pods}=    Get VM Launcher Pods    ${vm_name}
    ${running}=    Evaluate    [p for p in $pods if p['phase'] == 'Running']
    Length Should Be    ${running}    1
    ...    msg=VM ${vm_name} should have one running virt-launcher pod: ${pods}
    Should Contain    ${running}[0][claims]    ${volume_name}
    ...    msg=The running virt-launcher pod of VM ${vm_name} does not use ${volume_name}: ${running}[0]
