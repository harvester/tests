*** Settings ***
Documentation    Volume (PVC) Test Cases: basic lifecycle, custom replicas, from-image,
...    expand, image-backed multi-resize, and concurrent creation.
...    Groups needing an image share one image created once in suite setup.
Test Tags        storage    volume    pr-baseline

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/volume.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${VOL_TAG}             volume
${CONCURRENT_COUNT}    3
# Dynamic Variables
${IMAGE_NAME}          ${EMPTY}
${VOL_NAME}            ${EMPTY}
${VOL_REPLICA_NAME}    ${EMPTY}
${VOL_FROM_IMG}        ${EMPTY}
${VOL_EXPAND}          ${EMPTY}
${VOL_RESIZE}          ${EMPTY}
${BASE_GI}             ${EMPTY}
@{VOL_NAMES}           @{EMPTY}


*** Test Cases ***
Create Volume And Verify Bound
    [Tags]    p0
    [Documentation]    Create a 10Gi volume with the default storage class and verify it becomes Bound
    When Create 10Gi Volume    ${VOL_NAME}
    And Wait Until Volume Is Active    ${VOL_NAME}
    Then Volume Size Is 10Gi    ${VOL_NAME}

Create Volume With Custom Replicas
    [Tags]    p1
    [Documentation]    Create a volume requesting a single replica and verify it becomes Bound
    When Create Volume    ${VOL_REPLICA_NAME}    size=5Gi    replicas=1
    And Wait Until Volume Is Active    ${VOL_REPLICA_NAME}
    Then Volume Size Is 5Gi    ${VOL_REPLICA_NAME}

List Volumes
    [Tags]    p1
    [Documentation]    Listed volumes should contain the volumes created in this suite
    Given Volume Is Present    ${VOL_NAME}
    And Volume Is Present    ${VOL_REPLICA_NAME}
    Then Volume Should Be Listed    ${VOL_NAME}
    And Volume Should Be Listed    ${VOL_REPLICA_NAME}

Delete Volume
    [Tags]    p0
    [Documentation]    Delete a volume and verify the resource is reclaimed
    Given Volume Is Present    ${VOL_REPLICA_NAME}
    When Delete Volume    ${VOL_REPLICA_NAME}
    Then Wait Until Volume Is Deleted    ${VOL_REPLICA_NAME}

Create Volume From Image And Verify Bound
    [Tags]    p0    smoke
    [Documentation]    Provision a volume from a VM image; it must bind and be
    ...    annotated with the source image id.
    When Create Volume From Image    ${VOL_FROM_IMG}    ${IMAGE_NAME}
    And Wait Until Volume Is Active    ${VOL_FROM_IMG}
    Then Volume Image Id Should Be    ${VOL_FROM_IMG}    ${DEFAULT_NAMESPACE}/${IMAGE_NAME}

Delete Volume From Image
    [Tags]    p0
    [Documentation]    Delete the image-backed volume and verify it is reclaimed
    Given Volume Is Present    ${VOL_FROM_IMG}
    When Delete Volume    ${VOL_FROM_IMG}
    Then Wait Until Volume Is Deleted    ${VOL_FROM_IMG}

Expand Volume Size
    [Tags]    p0    expand
    [Documentation]    Create a 10Gi volume and expand it to 20Gi
    Given Create 10Gi Volume    ${VOL_EXPAND}
    And Wait Until Volume Is Active    ${VOL_EXPAND}
    And Volume Size Is 10Gi    ${VOL_EXPAND}
    When Update Volume Size to 20Gi    ${VOL_EXPAND}
    And Wait Until Volume Is Active    ${VOL_EXPAND}
    Then Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is 20Gi    ${VOL_EXPAND}

Create Image-Backed Volume And Verify Bound
    [Tags]    p0    resize
    [Documentation]    Provision a volume from a VM image and capture its base size
    When Create Volume From Image    ${VOL_RESIZE}    ${IMAGE_NAME}
    And Wait Until Volume Is Active    ${VOL_RESIZE}
    Then Capture Base Volume Size    ${VOL_RESIZE}

Resize Image-Backed Volume Multiple Times
    [Tags]    p0    resize    sanity
    [Documentation]    Expand the volume twice (base+5Gi, then base+10Gi); it must
    ...    reflect each new size and stay Bound throughout.
    Given Volume Is Present    ${VOL_RESIZE}
    ${first}=     Evaluate    ${BASE_GI} + 5
    ${second}=    Evaluate    ${BASE_GI} + 10
    When Expand Volume And Verify    ${VOL_RESIZE}    ${first}
    And Expand Volume And Verify    ${VOL_RESIZE}    ${second}

Create Volumes Concurrently And Verify Bound
    [Tags]    p2
    [Documentation]    Create ${CONCURRENT_COUNT} volumes in parallel; all must
    ...    succeed, reach Bound, then delete cleanly in parallel.
    ${results}=    Create Volumes Concurrently    ${VOL_NAMES}
    All Volume Operations Should Succeed    ${results}
    Length Should Be    ${results}    ${CONCURRENT_COUNT}
    FOR    ${vol_name}    IN    @{VOL_NAMES}
        Volume Phase Is Bound    ${vol_name}
    END
    ${cleanup}=    Delete Volumes Concurrently    ${VOL_NAMES}
    All Volume Operations Should Succeed    ${cleanup}


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    ${VOL_TAG}
    Set Suite Variable    ${IMAGE_NAME}          img-${suffix}
    Set Suite Variable    ${VOL_NAME}            vol-${suffix}
    Set Suite Variable    ${VOL_REPLICA_NAME}    vol-r-${suffix}
    Set Suite Variable    ${VOL_FROM_IMG}        vol-img-${suffix}
    Set Suite Variable    ${VOL_EXPAND}          vol-exp-${suffix}
    Set Suite Variable    ${VOL_RESIZE}          vol-rsz-${suffix}
    @{names}=    Create List
    FOR    ${i}    IN RANGE    ${CONCURRENT_COUNT}
        Append To List    ${names}    vol-conc-${i}-${suffix}
    END
    Set Suite Variable    @{VOL_NAMES}    @{names}
    Set up test environment
    # One shared image for the from-image and resize groups
    Image is available for VM creation    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}

Capture Base Volume Size
    [Arguments]    ${vol_name}
    [Documentation]    Read the bound volume's size (e.g. "10Gi") and store the GiB int
    ${size}=    Get Volume Size    ${vol_name}
    ${base_gi}=    Evaluate    int("${size}".rstrip("GiB"))
    Set Suite Variable    ${BASE_GI}    ${base_gi}
    Log    Image-backed volume base size is ${base_gi}Gi

Expand Volume And Verify
    [Arguments]    ${vol_name}    ${new_gi}
    [Documentation]    Expand to ${new_gi}Gi and confirm the size sticks and stays Bound
    Update Volume Size to ${new_gi}Gi    ${vol_name}
    Wait Until Volume Is Active    ${vol_name}
    Wait Until Keyword Succeeds    ${WAIT_TIMEOUT}    ${RETRY_INTERVAL}
    ...    Volume Size Is ${new_gi}Gi    ${vol_name}

Local Suite Teardown
    # Parallel-safe: only delete this suite's own named resources (never a global
    # label sweep, which would remove volumes owned by sibling suites under pabot).
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Delete Volume    ${VOL_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_REPLICA_NAME}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_FROM_IMG}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_EXPAND}
    Run Keyword And Ignore Error    Delete Volume    ${VOL_RESIZE}
    FOR    ${vol_name}    IN    @{VOL_NAMES}
        Run Keyword And Ignore Error    Delete Volume    ${vol_name}
    END
    Run Keyword And Ignore Error    Delete image by name    ${IMAGE_NAME}
