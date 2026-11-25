*** Settings ***
Documentation    Image encryption and decryption on Longhorn v2 (harvester/harvester#7523,
...    PR harvester/harvester#11922, backport harvester/harvester#12371)
...    An LHv2 image uses the CDI backend, so encrypting or decrypting it clones the
...    image PVC onto the target StorageClass (sourceType clone). Covers:
...    - encrypt an LHv2 image onto an encrypted LHv2 StorageClass and decrypt it back
...    - the Longhorn volumes are (not) encrypted, the source image stays unchanged
...    - VMs boot from the encrypted and the decrypted image, and the data of their root
...      disks is (not) encrypted on the node's raw block device
...    - the webhook rejects invalid requests: re-encrypt / re-decrypt, wrong target
...      encryption, LHv1 <-> LHv2, backing image <-> CDI backend, missing source or
...      StorageClass, changed securityParameters
...    The suite enables the LHv2 data engine if needed, reuses a provisioned LHv2 disk
...    (or provisions a free NVMe disk) and creates its own StorageClasses.
...    Requires an LHv2 disk of at least 70 GiB per node: the suite creates five volumes
...    of the image size or 10 GiB (source, encrypted and decrypted image, two VM root
...    disks), and Longhorn also keeps 25% of the disk free.
Test Tags        image    encryption    lhv2

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/volume.resource
Resource    ../../../keywords/setting.resource
Resource    ../../../keywords/storage.resource
Resource    ../../../keywords/storageclass.resource
Library     pabot.PabotLib

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${SUFFIX}              ${EMPTY}
${SECRET_NAME}         ${EMPTY}
${LHV2_SC}             ${EMPTY}
${LHV2_ENC_SC}         ${EMPTY}
${LHV1_ENC_SC}         ${EMPTY}
${LHV1_IMG_NAME}       ${EMPTY}
${SRC_IMG_NAME}        ${EMPTY}
${ENC_IMG_NAME}        ${EMPTY}
${DEC_IMG_NAME}        ${EMPTY}
${VM_NAME}             ${EMPTY}
${DEC_VM_NAME}         ${EMPTY}
&{PROVISIONED_DISKS}


*** Test Cases ***
Encrypt LHv2 Image
    [Tags]    p0    issue-7523
    When Image is encrypted from    ${ENC_IMG_NAME}    ${SRC_IMG_NAME}    ${LHV2_ENC_SC}
    ...    backend=cdi
    Then Image Security Parameters Should Be    ${ENC_IMG_NAME}    encrypt    ${SRC_IMG_NAME}
    And Image Storage Class Name Should Be    ${ENC_IMG_NAME}    ${LHV2_ENC_SC}
    And Image Virtual Size Should Equal    ${ENC_IMG_NAME}    ${SRC_IMG_NAME}
    # A CDI image stores its data in a PVC named like the image
    And Longhorn Volume Of PVC Encryption Should Be    ${ENC_IMG_NAME}    ${TRUE}    v2
    And Longhorn Volume Of PVC Encryption Should Be    ${SRC_IMG_NAME}    ${FALSE}    v2
    And Image State Is Active    ${SRC_IMG_NAME}

Decrypt Encrypted LHv2 Image
    [Tags]    p0    issue-7523
    Given Image State Is Active    ${ENC_IMG_NAME}
    When Image is decrypted from    ${DEC_IMG_NAME}    ${ENC_IMG_NAME}    ${LHV2_SC}
    ...    backend=cdi
    Then Image Security Parameters Should Be    ${DEC_IMG_NAME}    decrypt    ${ENC_IMG_NAME}
    And Image Storage Class Name Should Be    ${DEC_IMG_NAME}    ${LHV2_SC}
    And Image Virtual Size Should Equal    ${DEC_IMG_NAME}    ${SRC_IMG_NAME}
    And Longhorn Volume Of PVC Encryption Should Be    ${DEC_IMG_NAME}    ${FALSE}    v2
    And Longhorn Volume Of PVC Encryption Should Be    ${ENC_IMG_NAME}    ${TRUE}    v2

VM Boots From Encrypted LHv2 Image
    [Tags]    p0    issue-7523
    [Documentation]    The root disk is provisioned on the image's encrypted StorageClass.
    ...    The guest agent only connects if the guest boots from the decrypted data.
    Given Image State Is Active    ${ENC_IMG_NAME}
    When VM is created    ${VM_NAME}    ${ENC_IMG_NAME}    1    1Gi
    ...    disk_access_mode=ReadWriteOnce
    Then VM should be running    ${VM_NAME}
    And VM qemu-agent should be connected    ${VM_NAME}
    And Longhorn Volume Of PVC Encryption Should Be    ${VM_NAME}-disk-0    ${TRUE}    v2
    And Data Of Attached PVC Should Be Encrypted On Disk    ${VM_NAME}-disk-0

VM Boots From Decrypted LHv2 Image
    [Tags]    p0    issue-7523
    [Documentation]    The data survives encrypt and decrypt, and is plain on disk again.
    ...    Also the control for the on-disk check of the encrypted image.
    Given Image State Is Active    ${DEC_IMG_NAME}
    When VM is created    ${DEC_VM_NAME}    ${DEC_IMG_NAME}    1    1Gi
    ...    disk_access_mode=ReadWriteOnce
    Then VM should be running    ${DEC_VM_NAME}
    And VM qemu-agent should be connected    ${DEC_VM_NAME}
    And Longhorn Volume Of PVC Encryption Should Be    ${DEC_VM_NAME}-disk-0    ${FALSE}    v2
    And Data Of Attached PVC Should Be Plain On Disk    ${DEC_VM_NAME}-disk-0

Re-Encrypting An Encrypted LHv2 Image Is Rejected
    [Tags]    p1    negative    issue-7523
    Given Image State Is Active    ${ENC_IMG_NAME}
    Then Image Crypto Operation Should Be Rejected    rej-reenc-${SUFFIX}    encrypt
    ...    ${ENC_IMG_NAME}    ${LHV2_ENC_SC}    can not re-encrypt

Decrypting An Unencrypted LHv2 Image Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-redec-${SUFFIX}    decrypt
    ...    ${SRC_IMG_NAME}    ${LHV2_SC}    can not re-decrypt

Encrypting Onto An Unencrypted StorageClass Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-enc-plain-${SUFFIX}    encrypt
    ...    ${SRC_IMG_NAME}    ${LHV2_SC}    is not configured for encryption

Decrypting Onto An Encrypted StorageClass Is Rejected
    [Tags]    p1    negative    issue-7523
    Given Image State Is Active    ${ENC_IMG_NAME}
    Then Image Crypto Operation Should Be Rejected    rej-dec-enc-${SUFFIX}    decrypt
    ...    ${ENC_IMG_NAME}    ${LHV2_ENC_SC}    requires an unencrypted target StorageClass

Encrypting An LHv2 Image Onto An LHv1 StorageClass Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-v2-v1-${SUFFIX}    encrypt
    ...    ${SRC_IMG_NAME}    ${LHV1_ENC_SC}    must use the same Longhorn data engine

Encrypting An LHv1 Image Onto An LHv2 StorageClass Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-v1-v2-${SUFFIX}    encrypt
    ...    ${LHV1_IMG_NAME}    ${LHV2_ENC_SC}    must use the same Longhorn data engine
    ...    backend=backingimage

Encrypting Into A Different Image Backend Is Rejected
    [Tags]    p1    negative    issue-7523
    [Documentation]    The LHv2 source image uses the CDI backend, the target backingimage
    Then Image Crypto Operation Should Be Rejected    rej-backend-${SUFFIX}    encrypt
    ...    ${SRC_IMG_NAME}    ${LHV2_ENC_SC}    source and target image backends must match
    ...    backend=backingimage

Encrypting Onto A Missing StorageClass Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-no-sc-${SUFFIX}    encrypt
    ...    ${SRC_IMG_NAME}    sc-missing-${SUFFIX}    not found

Encrypting A Missing Source Image Is Rejected
    [Tags]    p1    negative    issue-7523
    Then Image Crypto Operation Should Be Rejected    rej-no-src-${SUFFIX}    encrypt
    ...    img-missing-${SUFFIX}    ${LHV2_ENC_SC}    source image ${DEFAULT_NAMESPACE}/img-missing-${SUFFIX} not found

Security Parameters Of An Encrypted LHv2 Image Are Immutable
    [Tags]    p1    negative    issue-7523
    Given Image State Is Active    ${ENC_IMG_NAME}
    &{security}=    Create Dictionary    cryptoOperation=decrypt
    ...    sourceImageName=${SRC_IMG_NAME}    sourceImageNamespace=${DEFAULT_NAMESPACE}
    ${result}=    When Try To Update Image Spec    ${ENC_IMG_NAME}    securityParameters=${security}
    Then Operation Should Be Rejected    ${result}    securityParameters cannot be modified


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${SUFFIX}           ${suffix}
    Set Suite Variable    ${SECRET_NAME}      enc-${suffix}
    Set Suite Variable    ${LHV2_SC}          sc-lhv2-${suffix}
    Set Suite Variable    ${LHV2_ENC_SC}      sc-lhv2-enc-${suffix}
    Set Suite Variable    ${LHV1_ENC_SC}      sc-lhv1-enc-${suffix}
    Set Suite Variable    ${LHV1_IMG_NAME}    img-lhv1-${suffix}
    Set Suite Variable    ${SRC_IMG_NAME}     img-lhv2-${suffix}
    Set Suite Variable    ${ENC_IMG_NAME}     img-lhv2-enc-${suffix}
    Set Suite Variable    ${DEC_IMG_NAME}     img-lhv2-dec-${suffix}
    Set Suite Variable    ${VM_NAME}          vm-lhv2-enc-${suffix}
    Set Suite Variable    ${DEC_VM_NAME}      vm-lhv2-dec-${suffix}
    # Encryption, the image/storageclass/volume helpers used here are CRD only
    Skip If    '%{HARVESTER_OPERATION_STRATEGY=crd}'.lower() == 'rest'
    ...    The LHv2 encryption setup needs the CRD operation strategy
    Set up test environment
    ${supported}=    Cluster Version Is At Least    1.10.0
    Skip If    not ${supported}    LHv2 image encryption is available since v1.10.0
    # Serialize with other suites using free NVMe disks, released in the teardown
    Acquire Lock    ${LHV2_DISK_LOCK}
    ${disks}=    Create LHv2 Storage Class With Provisioned Disks    ${LHV2_SC}
    Set Suite Variable    ${PROVISIONED_DISKS}    ${disks}
    # Same replica count as the plain LHv2 StorageClass, i.e. one per LHv2 disk
    ${replicas}=    Get Storage Class Parameter    ${LHV2_SC}    numberOfReplicas
    Create Encryption Secret    ${SECRET_NAME}    ${SECRET_NAME}-passphrase
    Create Encrypted Storage Class    ${LHV2_ENC_SC}    v2    ${replicas}    ${SECRET_NAME}
    Create Encrypted Storage Class    ${LHV1_ENC_SC}    v1    1    ${SECRET_NAME}
    Image is available for VM creation    ${SRC_IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    ...    storage_class=${LHV2_SC}
    Image is available for VM creation    ${LHV1_IMG_NAME}    ${OPENSUSE_IMAGE_URL}

Local Suite Teardown
    # Always clean up: leftover volumes of a failed run fill the LHv2 disk and make
    # the next run fail as well. The details are in the robot log.
    Run Keyword If Any Tests Failed    Log Variables
    Delete Suite Resources
    Run Keyword And Ignore Error    Release Lock    ${LHV2_DISK_LOCK}

Delete Suite Resources
    Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
    Run Keyword And Ignore Error    VM is deleted    ${DEC_VM_NAME}
    # The webhook blocks deleting an image whose PVC is a clone source or used by a VM
    FOR    ${image}    IN    ${DEC_IMG_NAME}    ${ENC_IMG_NAME}    ${SRC_IMG_NAME}
    ...    ${LHV1_IMG_NAME}
        Run Keyword And Ignore Error    Delete image by name    ${image}
        # The image is deleted asynchronously and still references the StorageClass
        Run Keyword And Ignore Error    Wait for image deleted by name    ${image}
    END
    Run Keyword And Ignore Error    Delete Storage Class    ${LHV2_ENC_SC}
    Run Keyword And Ignore Error    Delete Storage Class    ${LHV1_ENC_SC}
    Run Keyword And Ignore Error    Delete Storage Class    ${LHV2_SC}
    Run Keyword And Ignore Error    Delete Encryption Secret    ${SECRET_NAME}
    # host/test_longhorn_v2.robot needs unprovisioned disks, reused disks stay untouched
    Run Keyword And Ignore Error    Unprovision Storages    ${PROVISIONED_DISKS}
