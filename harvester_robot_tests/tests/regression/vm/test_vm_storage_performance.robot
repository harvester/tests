*** Settings ***
Documentation    VM Storage Performance Test Cases
...    Covers the KubeVirt high-performance storage options that the Harvester
...    UI exposes since v1.9.1 (harvester/harvester#11550):
...    - per disk: cache mode, I/O mode and a dedicated I/O thread
...    - per VM: virtio-blk multi-queue and the I/O threads policy
...    Each case creates a VM with the options set, then checks that they are
...    kept in the VM spec, reach the running VMI and that the guest boots.
Test Tags        virtualmachines    volumes    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Setup        Skip Before Harvester 1.9.0
Test Teardown     Common Test Teardown


*** Variables ***
# StorageClass for the test image and data disks. Empty uses the cluster
# defaults; override (e.g. --variable IMAGE_STORAGE_CLASS:lvm-thin) on clusters
# whose default storage cannot fit the test volumes.
${IMAGE_STORAGE_CLASS}    ${EMPTY}

# Dynamic Variables
${SUFFIX}          ${EMPTY}
${IMG_NAME}        ${EMPTY}
${SSH_PUB_KEY}     ${EMPTY}
${SSH_PRI_KEY}     ${EMPTY}
@{CREATED_VMS}


*** Test Cases ***
Create VM With No Host Cache And Native IO
    [Tags]    p0
    [Documentation]    The "High Performance" profile: cache=none, io=native and a
    ...    dedicated I/O thread on the boot disk. The options must be kept in
    ...    the VM spec and the running VMI, and the guest must boot and write.
    ${vm}=    Storage Performance VM Is Created    hp
    ...    boot_disk_options=${{ {"cache": "none", "io": "native", "dedicated_io_thread": True} }}
    VM Disk Performance Should Be    ${vm}    disk-0
    ...    cache=none    io=native    dedicatedIOThread=True
    VM Should Boot And Write To Disk    ${vm}
    VM Disk Performance Should Be    ${vm}    disk-0    from_vmi=${True}
    ...    cache=none    io=native    dedicatedIOThread=True

Create VM With Writeback Cache And Threads IO
    [Tags]    p1
    [Documentation]    A custom profile with the host page cache enabled:
    ...    cache=writeback and io=threads on the boot disk and on a data disk.
    ${data_disk}=    Create Dictionary    size=2Gi    cache=writeback    io=threads
    IF    "${IMAGE_STORAGE_CLASS}"
        # The override is typically node-local storage (e.g. LVM), which
        # cannot provision ReadWriteMany volumes
        Set To Dictionary    ${data_disk}    storage_class=${IMAGE_STORAGE_CLASS}
        ...    access_mode=ReadWriteOnce
    END
    @{extra_disks}=    Create List    ${data_disk}
    ${vm}=    Storage Performance VM Is Created    wb
    ...    boot_disk_options=${{ {"cache": "writeback", "io": "threads"} }}
    ...    extra_disks=${extra_disks}
    VM Disk Performance Should Be    ${vm}    disk-0    cache=writeback    io=threads
    VM Disk Performance Should Be    ${vm}    ${vm}-disk-1    cache=writeback    io=threads
    VM Should Boot And Write To Disk    ${vm}
    VM Disk Performance Should Be    ${vm}    ${vm}-disk-1    from_vmi=${True}
    ...    cache=writeback    io=threads
    # KubeVirt defaults block disks to cache=none/io=native on its own, so
    # seeing writeback/threads in the domain proves the setting reached QEMU
    VM Launched Disk Driver Should Be    ${vm}    disk-0    cache=writeback    io=threads
    VM Launched Disk Driver Should Be    ${vm}    ${vm}-disk-1    cache=writeback    io=threads

Create VM With Block Multi Queue
    [Tags]    p0
    [Documentation]    blockMultiQueue=true gives every virtio-blk disk one queue
    ...    per vCPU. The setting must reach the running VMI and the domain must
    ...    request one queue per vCPU. The guest is not checked: QEMU sizes the
    ...    virtio-blk queues to the vCPU count even with multi-queue off, so
    ...    the guest sees the same queue count either way.
    ${vm}=    Storage Performance VM Is Created    mq    cpu=2
    ...    block_multi_queue=${True}
    VM Domain IO Settings Should Be    ${vm}    blockMultiQueue=True
    VM Should Boot And Write To Disk    ${vm}
    VM Domain IO Settings Should Be    ${vm}    from_vmi=${True}    blockMultiQueue=True
    VM Launched Disk Driver Should Be    ${vm}    disk-0    queues=2

Create VM With Supplemental Pool IO Threads
    [Tags]    p1
    [Documentation]    ioThreadsPolicy=supplementalPool with an explicit thread
    ...    count, combined with a dedicated I/O thread on the boot disk.
    ${vm}=    Storage Performance VM Is Created    pool
    ...    boot_disk_options=${{ {"cache": "none", "io": "native", "dedicated_io_thread": True} }}
    ...    io_threads_policy=supplementalPool    supplemental_pool_thread_count=2
    VM Domain IO Settings Should Be    ${vm}
    ...    ioThreadsPolicy=supplementalPool    supplementalPoolThreadCount=2
    VM Should Boot And Write To Disk    ${vm}
    VM Domain IO Settings Should Be    ${vm}    from_vmi=${True}
    ...    ioThreadsPolicy=supplementalPool    supplementalPoolThreadCount=2

Create VM With Shared IO Threads Policy
    [Tags]    p2
    [Documentation]    ioThreadsPolicy=shared with a dedicated I/O thread disk,
    ...    which is what the UI sets when a disk asks for a dedicated thread
    ...    and no policy is chosen.
    ${vm}=    Storage Performance VM Is Created    shared
    ...    boot_disk_options=${{ {"dedicated_io_thread": True} }}
    ...    io_threads_policy=shared
    VM Should Boot And Write To Disk    ${vm}
    VM Domain IO Settings Should Be    ${vm}    from_vmi=${True}    ioThreadsPolicy=shared
    VM Disk Performance Should Be    ${vm}    disk-0    from_vmi=${True}    dedicatedIOThread=True

VM With Native IO And Writeback Cache Does Not Start
    [Tags]    p1    negative
    [Documentation]    io=native needs cache=none (or directsync). KubeVirt only
    ...    validates each value on its own, so the VM is accepted, but libvirt
    ...    refuses to start the domain. The VM must report the libvirt error in
    ...    its Synchronized condition instead of reaching Running. The UI
    ...    prevents this combination by forcing cache=none for io=native.
    ${vm}=    Storage Performance VM Is Created    bad
    ...    boot_disk_options=${{ {"cache": "writeback", "io": "native"} }}
    VM Disk Performance Should Be    ${vm}    disk-0    cache=writeback    io=native
    ${condition}=    VM condition should be    ${vm}    Synchronized    False
    Should Contain    ${condition}[message]    io='native' needs either no disk cache
    ...    msg=VM ${vm} failed to start for another reason: ${condition}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${SUFFIX}      ${suffix}
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Set up test environment
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${IMAGE_STORAGE_CLASS}
    ${pub}    ${pri}=    Generate SSH Keypair
    Set Suite Variable    ${SSH_PUB_KEY}    ${pub}
    Set Suite Variable    ${SSH_PRI_KEY}    ${pri}

Local Suite Teardown
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    FOR    ${vm}    IN    @{CREATED_VMS}
        Run Keyword And Ignore Error    VM is deleted    ${vm}
    END
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}

Skip Before Harvester 1.9.0
    ${supported}=    Cluster Version Is At Least    1.9.0
    Skip If    not ${supported}
    ...    These cases are verified on Harvester v1.9.0 and later

Storage Performance VM Is Created
    [Arguments]    ${name}    ${cpu}=1    &{options}
    [Documentation]    Create a VM with the guest SSH key and the given storage
    ...    performance options, and register it for suite cleanup.
    ${vm}=    Set Variable    vm-${name}-${SUFFIX}
    VM is created    ${vm}    ${IMG_NAME}    ${cpu}    2Gi
    ...    ssh_public_key=${SSH_PUB_KEY}    &{options}
    Append To List    ${CREATED_VMS}    ${vm}
    RETURN    ${vm}

VM Should Boot And Write To Disk
    [Arguments]    ${vm}
    [Documentation]    Wait for the guest to boot, then write and read back data
    ...    with O_DIRECT so the I/O goes through the configured disk path.
    VM should be running    ${vm}
    VM should have IP addresses    ${vm}
    VM cloud-init should be done    ${vm}    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${output}=    Execute Command In VM    ${vm}
    ...    sudo dd if=/dev/urandom of=/var/tmp/perf-check bs=1M count=16 oflag=direct status=none && sudo sha256sum /var/tmp/perf-check | cut -c1-8
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    Should Match Regexp    ${output.strip()}    ^[0-9a-f]{8}$
    ...    msg=Failed to write to the disk of ${vm}: ${output}
