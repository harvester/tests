*** Settings ***
Documentation    VM Storage Migration Test Cases
...    Storage migration moves a volume of a running VM to another PVC (for
...    example on another StorageClass) with a KubeVirt volume migration.
...    After the migration the source PVC is no longer used by the VM and must
...    be deletable while the VM keeps running (harvester/harvester#12132):
...    KubeVirt keeps the migration source virt-launcher pod in the Succeeded
...    phase until the VMI goes away, and that pod still lists the source PVC,
...    so Harvester has to remove it to release the PVC.
...    Both cases live-migrate the VM and need at least two nodes.
Test Tags        virtualmachines    volumes    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/host.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# StorageClass of the migrated data disk (source) and of the empty PVC it is
# migrated to (target). Using different classes (e.g. Longhorn -> a CSI SAN
# driver) matches the usual reason for a storage migration; the same class
# works too. The source must allow the VM to live-migrate (ReadWriteMany).
${SMIG_SOURCE_STORAGE_CLASS}    ${DEFAULT_STORAGE_CLASS}
${SMIG_TARGET_STORAGE_CLASS}    ${DEFAULT_STORAGE_CLASS}
${SMIG_TARGET_ACCESS_MODE}      ReadWriteMany
# StorageClass for the test image (boot disk). Empty uses the cluster default.
# The boot disk is not migrated, so it must also be ReadWriteMany.
${IMAGE_STORAGE_CLASS}          ${EMPTY}
# Size of the migrated data disk. The guest finds the disk by this size, so
# keep it different from the 10Gi boot disk.
${SMIG_DISK_SIZE}               3Gi
${SMIG_DISK_BYTES}              3221225472
# How long Harvester may take to release the source PVC once the migration
# has completed.
${PVC_RELEASE_TIMEOUT}          180

# Dynamic Variables
${IMG_NAME}        ${EMPTY}
${SSH_PUB_KEY}     ${EMPTY}
${SSH_PRI_KEY}     ${EMPTY}
${VM_SMIG}         ${EMPTY}
${VM_LM}           ${EMPTY}
${TARGET_PVC}      ${EMPTY}


*** Test Cases ***
Source Volume Is Released After Storage Migration
    [Tags]    p0    multinode
    [Documentation]    Migrate the data disk of a running VM to an empty PVC.
    ...    Once the migration has completed, no virt-launcher pod of the VM
    ...    may still reference the source PVC (the Completed migration source
    ...    pod is removed), and deleting the source PVC must finish while the
    ...    VM keeps running on the target PVC with its data intact.
    ...    harvester/harvester#12132
    ${vm}=    Set Variable    ${VM_SMIG}
    ${source}=    Set Variable    ${vm}-disk-1
    ${data_disk}=    Create Dictionary    size=${SMIG_DISK_SIZE}    storage_class=${SMIG_SOURCE_STORAGE_CLASS}
    @{extra_disks}=    Create List    ${data_disk}
    VM is created    ${vm}    ${IMG_NAME}    1    2Gi    ssh_public_key=${SSH_PUB_KEY}
    ...    extra_disks=${extra_disks}
    VM should be running    ${vm}
    VM should have IP addresses    ${vm}
    VM cloud-init should be done    ${vm}    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${checksum}=    Data Is Written To Data Disk    ${vm}

    Create Volume    ${TARGET_PVC}    ${SMIG_DISK_SIZE}    storage_class=${SMIG_TARGET_STORAGE_CLASS}
    ...    access_mode=${SMIG_TARGET_ACCESS_MODE}
    Start Storage Migration    ${vm}    ${source}    ${TARGET_PVC}
    Storage Migration Should Complete    ${vm}    ${source}    ${TARGET_PVC}
    VM Should Run Only On Volume    ${vm}    ${TARGET_PVC}

    # The fix: the Completed migration source pod is deleted, which releases
    # the source PVC without stopping the VM
    Wait Until Keyword Succeeds    ${PVC_RELEASE_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM Launcher Pods Should Not Use Volume    ${vm}    ${source}
    Volume Should Be Released    ${source}    timeout=${PVC_RELEASE_TIMEOUT}
    Delete Volume And Wait    ${source}    timeout=${PVC_RELEASE_TIMEOUT}

    VM should be running    ${vm}
    VM Should Run Only On Volume    ${vm}    ${TARGET_PVC}
    ${after}=    Data Disk Checksum    ${vm}
    Should Be Equal    ${after}    ${checksum}
    ...    msg=Data on the migrated disk of ${vm} changed: ${checksum} -> ${after}

Compute Live Migration Keeps Completed Source Pod
    [Tags]    p1    multinode
    [Documentation]    Regression check for the cleanup above: a regular live
    ...    migration (no volume change) leaves a Completed source pod that
    ...    references the same PVCs as the VM. It is not stale and must be
    ...    kept, as before.
    ${vm}=    Set Variable    ${VM_LM}
    VM is created    ${vm}    ${IMG_NAME}    1    2Gi
    VM should be running    ${vm}
    ${node}=    Get VM node    ${vm}
    VM is live-migrated    ${vm}
    VM should be moved off node    ${vm}    ${node}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    VM Should Have A Completed Launcher Pod    ${vm}
    # Give the Harvester controllers time to react to the finished pod
    Sleep    30s    reason=Let the VM and pod controllers reconcile the finished source pod
    VM Should Have A Completed Launcher Pod    ${vm}
    VM should be running    ${vm}


*** Keywords ***
Skip Unless Live Migration Is Possible
    [Documentation]    Storage migration is a KubeVirt live migration, and the
    ...    migration target pod has an anti-affinity to the source node, so
    ...    the suite needs at least two nodes.
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2
    ...    A live migration needs at least 2 nodes, the cluster has ${node_count}

Data Is Written To Data Disk
    [Arguments]    ${vm_name}
    [Documentation]    Write 16 MiB of random data to the start of the data
    ...    disk (found by its size) and return its checksum.
    ${output}=    Execute Command In VM    ${vm_name}
    ...    d=$(lsblk -dbno NAME,SIZE | awk '$2==${SMIG_DISK_BYTES}{print "/dev/"$1; exit}'); sudo dd if=/dev/urandom of=$d bs=1M count=16 oflag=direct status=none && sudo dd if=$d bs=1M count=16 iflag=direct status=none | sha256sum | cut -c1-16
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    Should Match Regexp    ${output.strip()}    ^[0-9a-f]{16}$
    ...    msg=Failed to write to the data disk of ${vm_name}: ${output}
    RETURN    ${output.strip()}

Data Disk Checksum
    [Arguments]    ${vm_name}
    [Documentation]    Return the checksum of the first 16 MiB of the data disk.
    ${output}=    Execute Command In VM    ${vm_name}
    ...    d=$(lsblk -dbno NAME,SIZE | awk '$2==${SMIG_DISK_BYTES}{print "/dev/"$1; exit}'); sudo dd if=$d bs=1M count=16 iflag=direct status=none | sha256sum | cut -c1-16
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    Should Match Regexp    ${output.strip()}    ^[0-9a-f]{16}$
    ...    msg=Failed to read the data disk of ${vm_name}: ${output}
    RETURN    ${output.strip()}

Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${IMG_NAME}      img-${suffix}
    Set Suite Variable    ${VM_SMIG}       vm-smig-${suffix}
    Set Suite Variable    ${VM_LM}         vm-lm-${suffix}
    Set Suite Variable    ${TARGET_PVC}    vol-smig-target-${suffix}
    Set up test environment
    Skip Unless Live Migration Is Possible
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${IMAGE_STORAGE_CLASS}
    ${pub}    ${pri}=    Generate SSH Keypair
    Set Suite Variable    ${SSH_PUB_KEY}    ${pub}
    Set Suite Variable    ${SSH_PRI_KEY}    ${pri}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    # VM is deleted also deletes the PVCs in the VM spec, which is the target
    # PVC once the migration has run; the source PVC is deleted separately
    Run Keyword If All Tests Passed    Run Keywords
    ...   Run Keyword And Ignore Error    VM is deleted    ${VM_SMIG}    AND
    ...   Run Keyword And Ignore Error    VM is deleted    ${VM_LM}    AND
    ...   Run Keyword And Ignore Error    Delete Volume    ${VM_SMIG}-disk-1    AND
    ...   Run Keyword And Ignore Error    Delete Volume    ${TARGET_PVC}    AND
    ...   Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
