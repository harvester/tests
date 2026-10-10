*** Settings ***
Documentation    Evaluate image import initiation followed by an independent image listing.
Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/rancher.resource
Resource    ../../../keywords/rancher_ai.resource
Resource    ../../../keywords/virtualmachine.resource

Suite Setup      Local Suite Setup
Test Tags        rancher-ai    images


*** Variables ***
${HARVESTER_CLUSTER_NAME}    ${EMPTY}
${HARVESTER_CLUSTER_ID}      c-m-sx8gk9lw    # ${EMPTY}
${PROMPT}      ${EMPTY}
${RESPONSE}    ${EMPTY}
${IMG_DISPLAY_NAME}          ${EMPTY}
${VM_NAME}    ${EMPTY}


*** Test Cases ***
List Virtual Machine Images
    When Prompt Rancher AI    List VM images
    Then Response Evaluation Should Pass    ${PROMPT}    ${RESPONSE}

Create Virtual Machine Image
    When Prompt Rancher AI    Create a VM image ${IMG_DISPLAY_NAME} using ${UBUNTU_IMAGE_URL}
    Then Response Evaluation Should Pass    ${PROMPT}    ${RESPONSE}
    ...   Check VM's display name instead of actual name
    And Image with display name ${IMG_DISPLAY_NAME} should exist

Get latest created VM image
    When Prompt Rancher AI    Get latest created VM image
    Then Response Evaluation Should Pass    ${PROMPT}    ${RESPONSE}
    ...    Shouls be ${IMG_DISPLAY_NAME}
    And Image with display name ${IMG_DISPLAY_NAME} should exist


Evaluate Response Demo: In the Context
    Run Keyword And Continue On Failure    Response Evaluation Should Pass
    ...    Create a VM image
    ...    An image ${IMG_DISPLAY_NAME} is downloading and you can use it once it is ready
    Run Keyword And Continue On Failure    Response Evaluation Should Fail
    ...    Create a VM image
    ...    Please provide the required VM image name and source URL to create an image

Evaluate Response Demo: Not In the Context 
    Run Keyword And Continue On Failure    Response Evaluation Should Fail
    ...    Create a VM image
    ...    A VM ${VM_NAME} is created
    Run Keyword And Continue On Failure    Response Evaluation Should Fail
    ...    Create a VM image
    ...    A VM network ${VM_NAME} is created
    Run Keyword And Continue On Failure    Response Evaluation Should Fail
    ...    Create a VM image
    ...    Unknown operation
    Run Keyword And Continue On Failure    Response Evaluation Should Fail
    ...    Create a VM image
    ...    Session expired


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    precise=${False}
    Set Suite Variable    ${IMG_DISPLAY_NAME}          img-${suffix}
    Set Suite Variable    ${HARVESTER_CLUSTER_NAME}    hvst-${suffix}
    Set Suite Variable    ${VM_NAME}                   vm-${suffix}
    Set up test environment

    IF    not $HARVESTER_CLUSTER_ID
        rancher.Import Harvester To Rancher In Setup
        Should Not Be Empty    ${HARVESTER_CLUSTER_ID}    Failed to import Harvester cluster
    END

Prompt Rancher AI
    [Arguments]    ${_prompt}
    ${conversation_result}=    rancher_ai.Prompt    ${_prompt}    ${HARVESTER_CLUSTER_ID}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}

# TODO: Setup rancher-ai-agent and harvester-mcp-server
# Ref. https://github.com/rancher/prime-docs/pull/362/changes
# rancher_keyword 裡有現有的 _run_kubectl 