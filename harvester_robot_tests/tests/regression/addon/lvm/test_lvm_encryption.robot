*** Settings ***
Documentation    LVM encryption at rest (harvester/harvester#11442,
...              harvester/csi-driver-lvm#67): an encrypted dm-thin
...              StorageClass references a CRYPTO_KEY_* secret, every volume
...              is LUKS2-formatted and opened on the node as the dm-crypt
...              mapping csi-lvm-<volume id>, and only ciphertext reaches the
...              backing LV. An encrypted class can neither be created
...              without its key secret nor lose it afterwards.
...              The host checks run the node's blkid/dmsetup/lsblk through a
...              transient privileged hostPID probe pod.
Test Tags        regression    addon    lvm    encryption

Resource         ../../../../keywords/lvm.resource
Resource         ../../../../keywords/workload.resource
Resource         ../../../../keywords/lvm_driver.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown


*** Variables ***
# StorageClass for the VM boot image. Empty uses the cluster default;
# override (e.g. -v IMAGE_STORAGE_CLASS:lvm-thin) on clusters whose default
# storage cannot fit it.
${IMAGE_STORAGE_CLASS}         ${EMPTY}
# Run against an LVM volume group that already exists instead of the one
# __init__.robot provisions: set the node (and -v LVM_VG_NAME:<vg>) when the
# suite is started on its own on a cluster whose addon is already in use.
${LVM_EXISTING_NODE}           %{LVM_EXISTING_NODE=}
# Prefix of the generated resource names.
${NAME_PREFIX}                 %{NAME_PREFIX=lvm-enc}
# Plaintext written by the consumers; must never show up on the raw LV.
${MARKER}                      ${EMPTY}

${LVM_SC_NAME}                 ${EMPTY}
${LVM_ORPHAN_SC_NAME}          ${EMPTY}
${LVM_REJECTED_SC_NAME}        ${EMPTY}
${LVM_SECRET_NAME}             ${EMPTY}
${LVM_ORPHAN_SECRET_NAME}      ${EMPTY}
${LVM_VOLUME_NAME}             ${EMPTY}
${LVM_VM_NAME}                 ${EMPTY}
${IMAGE_NAME}                  ${EMPTY}
${LVM_NODE_NAME}               ${EMPTY}
${SSH_PUB_KEY}                 ${EMPTY}
${SSH_PRI_KEY}                 ${EMPTY}


*** Test Cases ***
Encrypted StorageClass Provisions A LUKS2 Volume
    [Documentation]    A Block PVC from the encrypted class binds and its pod
    ...    starts. On the node the backing LV is a LUKS2 container opened as
    ...    the csi-lvm-<volume id> dm-crypt mapping, the consumer reads back
    ...    what it wrote through that mapping, and the plaintext never appears
    ...    on the raw LV.
    [Tags]    p0
    Create Volume
    ...    ${LVM_VOLUME_NAME}
    ...    ${LVM_VOLUME_SIZE}
    ...    storage_class=${LVM_SC_NAME}
    ...    volume_mode=Block
    ...    access_mode=ReadWriteOnce
    Create Workload Pod With Volume    ${POD_ENC}    ${LVM_VOLUME_NAME}    Block
    Wait Until Volume Is Active    ${LVM_VOLUME_NAME}
    Write Marker To Block Volume    ${POD_ENC}    ${MARKER}
    ${count}=    Block Volume Marker Count    ${POD_ENC}    ${MARKER}
    Should Be True    ${count} > 0    msg=The consumer cannot read back what it wrote
    LVM Volume Should Be Encrypted With LUKS2    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${LVM_VOLUME_NAME}
    Plaintext Should Not Reach The Backing LV
    ...    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${LVM_VOLUME_NAME}    ${MARKER}
    [Teardown]    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_ENC}

VM Writes To An Encrypted Volume
    [Documentation]    A VM with a data disk from the encrypted class boots and
    ...    writes to the disk; the guest reads its data back while the host
    ...    only holds ciphertext under a LUKS2 header.
    [Tags]    p0
    ${data_disk}=    Create Dictionary    size=2Gi    storage_class=${LVM_SC_NAME}
    ...    access_mode=ReadWriteOnce
    @{extra_disks}=    Create List    ${data_disk}
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${IMAGE_STORAGE_CLASS}
    VM is created    ${LVM_VM_NAME}    ${IMAGE_NAME}    1    2Gi
    ...    ssh_public_key=${SSH_PUB_KEY}    node_name=${LVM_NODE_NAME}
    ...    extra_disks=${extra_disks}
    VM should be running    ${LVM_VM_NAME}
    VM should have IP addresses    ${LVM_VM_NAME}
    VM cloud-init should be done    ${LVM_VM_NAME}    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${disk}=    Execute Command In VM    ${LVM_VM_NAME}
    ...    lsblk -dn -o NAME,SIZE | awk '$2=="2G"{print "/dev/"$1; exit}'
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    ${disk}=    Set Variable    ${disk.strip()}
    Should Start With    ${disk}    /dev/    msg=The 2Gi encrypted data disk is not visible in the guest
    ${output}=    Execute Command In VM    ${LVM_VM_NAME}
    ...    yes ${MARKER} | head -c 4194304 | sudo dd of=${disk} bs=1M oflag=direct status=none && sudo dd if=${disk} bs=1M count=4 iflag=direct status=none | grep -c ${MARKER}
    ...    ${OPENSUSE_SSH_USER}    pkey=${SSH_PRI_KEY}
    Should Match Regexp    ${output.strip()}    ^[1-9][0-9]*$
    ...    msg=The guest cannot read back what it wrote: ${output}
    LVM Volume Should Be Encrypted With LUKS2    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${LVM_VM_NAME}-disk-1
    Plaintext Should Not Reach The Backing LV
    ...    ${LVM_NODE_NAME}    ${LVM_VG_NAME}    ${LVM_VM_NAME}-disk-1    ${MARKER}

Encrypted StorageClass Is Rejected Without Its Key Secret
    [Documentation]    An encrypted class whose CRYPTO_KEY_* secret does not
    ...    exist is refused at admission, so no volume can be provisioned
    ...    without a key.
    [Tags]    p1    negative
    ${result}=    Try To Create Encrypted LVM Storage Class
    ...    ${LVM_REJECTED_SC_NAME}    ${LVM_VG_NAME}    ${LVM_VG_TYPE}    ${LVM_NODE_NAME}
    ...    ${LVM_REJECTED_SC_NAME}-missing
    Operation Should Be Rejected    ${result}    not found
    Storage Class Should Not Exist    ${LVM_REJECTED_SC_NAME}

Key Secret Of An Encrypted StorageClass Cannot Be Deleted
    [Documentation]    Once an encrypted class references a key secret, deleting
    ...    the secret is refused while the class exists, so volumes of the
    ...    class can never lose their key.
    [Tags]    p1    negative
    Create LVM Encryption Secret    ${LVM_ORPHAN_SECRET_NAME}    ${MARKER}-orphan
    Create Encrypted LVM Storage Class
    ...    ${LVM_ORPHAN_SC_NAME}    ${LVM_VG_NAME}    ${LVM_VG_TYPE}    ${LVM_NODE_NAME}
    ...    ${LVM_ORPHAN_SECRET_NAME}
    ${result}=    Try To Delete Secret    ${LVM_ORPHAN_SECRET_NAME}
    Operation Should Be Rejected    ${result}    used by encrypted storage classes
    Secret Should Exist    ${LVM_ORPHAN_SECRET_NAME}
    Delete Storage Class    ${LVM_ORPHAN_SC_NAME}
    Wait Until Storage Class Is Deleted    ${LVM_ORPHAN_SC_NAME}
    Delete Secret    ${LVM_ORPHAN_SECRET_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${NAME_PREFIX}
    Set Suite Variable    ${MARKER}                      LVMENCMARKER${suffix.replace('-', '')}
    Set Suite Variable    ${LVM_SC_NAME}                 lvm-sc-${suffix}
    Set Suite Variable    ${LVM_ORPHAN_SC_NAME}          lvm-orphan-sc-${suffix}
    Set Suite Variable    ${LVM_REJECTED_SC_NAME}        lvm-rejected-sc-${suffix}
    Set Suite Variable    ${LVM_SECRET_NAME}             lvm-key-${suffix}
    Set Suite Variable    ${LVM_ORPHAN_SECRET_NAME}      lvm-orphan-key-${suffix}
    Set Suite Variable    ${LVM_VOLUME_NAME}             lvm-vol-${suffix}
    Set Suite Variable    ${LVM_VM_NAME}                 lvm-vm-${suffix}
    Set Suite Variable    ${IMAGE_NAME}                  image-${suffix}
    Set Suite Variable    ${POD_ENC}                     pod-enc-${suffix}
    IF    "${LVM_EXISTING_NODE}"
        Set up test environment
        Set Suite Variable    ${LVM_NODE_NAME}    ${LVM_EXISTING_NODE}
    ELSE
        ${node}=    Initialize LVM Workload Suite
        Set Suite Variable    ${LVM_NODE_NAME}    ${node}
    END
    Create LVM Encryption Secret    ${LVM_SECRET_NAME}    ${MARKER}-passphrase
    Create Encrypted LVM Storage Class
    ...    ${LVM_SC_NAME}    ${LVM_VG_NAME}    ${LVM_VG_TYPE}    ${LVM_NODE_NAME}
    ...    ${LVM_SECRET_NAME}
    ${pub}    ${pri}=    Generate SSH Keypair
    Set Suite Variable    ${SSH_PUB_KEY}    ${pub}
    Set Suite Variable    ${SSH_PRI_KEY}    ${pri}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword And Ignore Error    VM is deleted    ${LVM_VM_NAME}
    Run Keyword And Ignore Error    Delete Workload Pod    ${POD_ENC}
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VM_NAME}-disk-1
    Run Keyword And Ignore Error    Delete Volume    ${LVM_VOLUME_NAME}
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_SC_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_ORPHAN_SC_NAME}
    Run Keyword And Ignore Error    Delete Storage Class    ${LVM_REJECTED_SC_NAME}
    Run Keyword And Ignore Error    Delete Secret    ${LVM_SECRET_NAME}
    Run Keyword And Ignore Error    Delete Secret    ${LVM_ORPHAN_SECRET_NAME}
