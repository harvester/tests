*** Settings ***
Documentation    VirtualMachineImage with a custom spec.backingImageName
...    (harvester/harvester#11641, backported to v1.9). The field pins the
...    Longhorn BackingImage and the StorageClass Harvester creates for the
...    image to one deterministic name instead of vmi-<uid> / lh-<uid>, so
...    GitOps manifests can reference the StorageClass before the image
...    exists. The suite skips on clusters whose VirtualMachineImage CRD
...    does not have the field.
Test Tags        image    backingimage    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/storageclass.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
# Dynamic Variables
${IMAGE_NAME}       ${EMPTY}
# The custom name; doubles as the Longhorn BackingImage and StorageClass name
${BI_NAME}          ${EMPTY}
${VM_NAME}          ${EMPTY}

*** Test Cases ***
Image With Custom Backing Image Name Uses It End To End
    [Tags]    p0
    [Documentation]    The image imported in Suite Setup with spec.backingImageName
    ...    must use the name end to end: status.storageClassName, the
    ...    StorageClass itself (whose backingImage parameter binds it to the
    ...    Longhorn BackingImage) and the Longhorn BackingImage CR all carry it.
    Given Image State Is Active    ${IMAGE_NAME}
    Then Image Storage Class Name Should Be    ${IMAGE_NAME}    ${BI_NAME}
    And Storage Class Is Present    ${BI_NAME}
    And Storage Class Parameter Should Be    ${BI_NAME}    backingImage    ${BI_NAME}
    And Backing Image Should Exist    ${BI_NAME}

VM Boots From Image With Custom Backing Image Name
    [Tags]    p0
    [Documentation]    A VM whose root disk is provisioned from the custom-named
    ...    StorageClass boots (qemu-agent connects), proving the StorageClass
    ...    really resolves to the BackingImage. The VM is removed at the end so
    ...    the image can be deleted afterwards.
    Given Image State Is Active    ${IMAGE_NAME}
    When VM is created    ${VM_NAME}    ${IMAGE_NAME}
    Then VM should be running    ${VM_NAME}
    And VM qemu-agent should be connected    ${VM_NAME}
    # A test-level teardown replaces the suite's Test Teardown, so run it
    # explicitly to keep Log Variables on failure.
    [Teardown]    Run Keywords    VM is deleted    ${VM_NAME}
    ...    AND    Common Test Teardown

Delete Image Removes Custom Storage Class And Backing Image
    [Tags]    p0
    [Documentation]    Deleting the image must remove the custom-named StorageClass
    ...    and Longhorn BackingImage. Harvester resolves the BackingImage to
    ...    delete by name, so this guards against the custom name being
    ...    ignored (leak) on the delete path.
    Given Image Should Exist    ${IMAGE_NAME}
    When Delete image by name    ${IMAGE_NAME}
    And Wait for image deleted by name    ${IMAGE_NAME}
    Then Wait Until Storage Class Is Deleted    ${BI_NAME}
    And Wait Until Backing Image Is Deleted    ${BI_NAME}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    custom-bi
    Set Suite Variable    ${IMAGE_NAME}    img-${suffix}
    Set Suite Variable    ${BI_NAME}       bi-${suffix}
    Set Suite Variable    ${VM_NAME}       vm-${suffix}
    Set up test environment
    Skip Unless Cluster Supports Custom Backing Image Name
    # Every test relies on this image holding ${BI_NAME}, so create it here
    # rather than in a test: tag filters (-i negative, -i p1) must not be
    # able to skip the precondition.
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}    backing_image_name=${BI_NAME}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources.
    # Keep the failure state for debugging; clean up only when all tests pass.
    Run Keyword If Any Tests Failed    Log Variables
    IF    '${SUITE STATUS}' == 'PASS'
        Run Keyword And Ignore Error    VM is deleted    ${VM_NAME}
        Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
    END
