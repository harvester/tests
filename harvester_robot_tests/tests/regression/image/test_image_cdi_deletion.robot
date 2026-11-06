*** Settings ***
Documentation    CDI image deletion protection for golden and cloned PVCs.
...    Covers harvester/harvester#12011 and PR #12188.
...    Set CDI_STORAGE_CLASS to an existing CDI-capable class, or set
...    CDI_STORAGE_BACKEND=lvm to provision storage for this suite.
...    The suite uses the CRD strategy.
Test Tags        regression    image    cdi    pr-baseline

Resource         ../../../keywords/image_deletion.resource
Resource         ../../../keywords/cdi_storage.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Teardown    Common Test Teardown


*** Variables ***
${STRATEGY}             %{HARVESTER_OPERATION_STRATEGY=crd}
${DIRECT_IMAGE}         ${EMPTY}
${DIRECT_VM}            ${EMPTY}
${CLONE_IMAGE}          ${EMPTY}
${CLONE_VM}             ${EMPTY}
${CLONE_PVC}            ${EMPTY}
${UNRELATED_PVC}        ${EMPTY}


*** Test Cases ***
Reject Image Deletion While VM Uses Golden PVC
    [Tags]    p0    negative
    [Documentation]    Reproduce VM importer output with the imported label and
    ...    a direct golden PVC reference. The actual VM import workflow is not run.
    ...    Running and stopped VMs block image deletion until the VM is removed.
    Image is available for VM creation
    ...    ${DIRECT_IMAGE}    ${OPENSUSE_IMAGE_URL}    storage_class=${CDI_STORAGE_CLASS}
    ${uid}=    Get PVC Identity    ${DIRECT_IMAGE}
    VM is created    ${DIRECT_VM}    ${DIRECT_IMAGE}    use_golden_image=${TRUE}
    VM should be running    ${DIRECT_VM}
    VM qemu-agent should be connected    ${DIRECT_VM}
    VM Should Use Golden PVC    ${DIRECT_VM}    ${DIRECT_IMAGE}
    Image Deletion Should Be Blocked
    ...    ${DIRECT_IMAGE}    its PVC is used by VM ${DEFAULT_NAMESPACE}/${DIRECT_VM}
    PVC Should Be Retained    ${DIRECT_IMAGE}    ${uid}
    DataVolume Should Be Complete    ${DIRECT_IMAGE}

    VM is stopped    ${DIRECT_VM}
    VM should be stopped    ${DIRECT_VM}
    Image Deletion Should Be Blocked
    ...    ${DIRECT_IMAGE}    its PVC is used by VM ${DEFAULT_NAMESPACE}/${DIRECT_VM}
    PVC Should Be Retained    ${DIRECT_IMAGE}    ${uid}
    VM is started    ${DIRECT_VM}
    VM should be running    ${DIRECT_VM}
    VM qemu-agent should be connected    ${DIRECT_VM}

    VM Is Deleted Keeping Volumes    ${DIRECT_VM}
    PVC Should Be Retained    ${DIRECT_IMAGE}    ${uid}
    Delete Unused Image    ${DIRECT_IMAGE}

Reject Image Deletion Until Completed Clone PVC Is Removed
    [Tags]    p0    negative
    [Documentation]    A completed clone blocks image deletion even after its VM
    ...    is stopped or removed. The VM must still boot after rejected deletion.
    ...    An unrelated PVC on the same storage class must not block deletion
    ...    once the clone PVC is gone.
    Image is available for VM creation
    ...    ${CLONE_IMAGE}    ${OPENSUSE_IMAGE_URL}    storage_class=${CDI_STORAGE_CLASS}
    VM is created    ${CLONE_VM}    ${CLONE_IMAGE}    boot_access_mode=ReadWriteOnce
    VM should be running    ${CLONE_VM}
    VM qemu-agent should be connected    ${CLONE_VM}
    VM Should Use Only PVC    ${CLONE_VM}    ${CLONE_PVC}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Clone Should Be Complete    ${CLONE_PVC}    ${CLONE_IMAGE}
    ${uid}=    Get PVC Identity    ${CLONE_PVC}
    Image Deletion Should Be Blocked
    ...    ${CLONE_IMAGE}    being used by clone PVC ${DEFAULT_NAMESPACE}/${CLONE_PVC}

    VM is stopped    ${CLONE_VM}
    VM should be stopped    ${CLONE_VM}
    Image Deletion Should Be Blocked
    ...    ${CLONE_IMAGE}    being used by clone PVC ${DEFAULT_NAMESPACE}/${CLONE_PVC}
    PVC Should Be Retained    ${CLONE_PVC}    ${uid}
    VM is started    ${CLONE_VM}
    VM should be running    ${CLONE_VM}
    VM qemu-agent should be connected    ${CLONE_VM}

    VM Is Deleted Keeping Volumes    ${CLONE_VM}
    PVC Should Be Retained    ${CLONE_PVC}    ${uid}
    Image Deletion Should Be Blocked
    ...    ${CLONE_IMAGE}    being used by clone PVC ${DEFAULT_NAMESPACE}/${CLONE_PVC}
    DataVolume Should Be Complete    ${CLONE_IMAGE}

    Create Volume    ${UNRELATED_PVC}    1Gi
    ...    storage_class=${CDI_STORAGE_CLASS}    access_mode=ReadWriteOnce
    Volume Is Present    ${UNRELATED_PVC}
    Delete volume    ${CLONE_PVC}
    Wait Until Volume Is Deleted    ${CLONE_PVC}
    Delete Unused Image    ${CLONE_IMAGE}
    Volume Is Present    ${UNRELATED_PVC}


*** Keywords ***
Local Suite Setup
    Skip If    '${STRATEGY}' != 'crd'    CDI deletion tests require the CRD strategy
    Skip If    $CDI_STORAGE_CLASS == '' and $CDI_STORAGE_BACKEND == 'none'
    ...    Set CDI_STORAGE_CLASS or CDI_STORAGE_BACKEND=lvm to run CDI deletion tests
    Set Up CDI Test Environment
    Prepare CDI Storage
    ${suffix}=    Generate Unique Name    cdi-delete
    Set Suite Variable    ${DIRECT_IMAGE}     direct-img-${suffix}
    Set Suite Variable    ${DIRECT_VM}        direct-vm-${suffix}
    Set Suite Variable    ${CLONE_IMAGE}      clone-img-${suffix}
    Set Suite Variable    ${CLONE_VM}         clone-vm-${suffix}
    Set Suite Variable    ${CLONE_PVC}        ${CLONE_VM}-disk-0
    Set Suite Variable    ${UNRELATED_PVC}    unrelated-${suffix}

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Delete Suite Resources
    Cleanup CDI Storage

Delete Suite Resources
    FOR    ${vm}    IN    ${DIRECT_VM}    ${CLONE_VM}
        IF    '${vm}' != '${EMPTY}'
            Run Keyword And Ignore Error    VM Is Deleted Keeping Volumes    ${vm}
        END
    END
    FOR    ${pvc}    IN    ${CLONE_PVC}    ${UNRELATED_PVC}
        IF    '${pvc}' != '${EMPTY}'
            Run Keyword And Ignore Error    Delete volume    ${pvc}
        END
    END
    FOR    ${image}    IN    ${DIRECT_IMAGE}    ${CLONE_IMAGE}
        IF    '${image}' != '${EMPTY}'
            Run Keyword And Ignore Error    Delete Unused Image    ${image}
        END
    END
