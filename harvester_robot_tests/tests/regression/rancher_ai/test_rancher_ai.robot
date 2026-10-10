*** Settings ***
Documentation    Evaluate image import initiation followed by an independent image listing.
Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/rancher.resource
Resource    ../../../keywords/rancher_ai.resource
Resource    ../../../keywords/host.resource
Resource   ../../../keywords/volume.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Tags        rancher-ai


# TODO: Support Ollama LLM
*** Variables ***
${HARVESTER_CLUSTER_NAME}    ${EMPTY}
${HARVESTER_CLUSTER_ID}      c-m-sx8gk9lw    # ${EMPTY}
${PROMPT}      ${EMPTY}
${RESPONSE}    ${EMPTY}
${IMG_DISPLAY_NAME}    ubuntu-24.04-server-cloudimg-amd64    # ${EMPTY}
${VM_NAME}      ${EMPTY}
${VNET_NAME}    vlan2011    # ${EMPTY}
${VOL_NAME}    ${EMPTY}


*** Test Cases ***
List Nodes
    [Tags]    node    tool:list_nodes
    ${node_count}=    Get cluster node count

    When Prompt Rancher    List nodes
    Then Rancher should reply    Found ${node_count} nodes in cluster

List Cluster Networks
    [Tags]    network    tool:list_cluster_networks

    When Prompt Rancher    List cluster networks
    Then Rancher should reply    Cluster has at least one network `mgmt`

List VM Networks
    [Tags]    network    tool:list_virtual_machine_networks

    Given network.Create VLAN Network    ${VNET_NAME}    ${VLAN_ID}    mgmt
    When Prompt Rancher    List VM networks
    Then Rancher should reply    Cluster has a vm network ${VNET_NAME}

Create VM Image
    [Tags]    image    tool:create_virtual_machine_image

    When Prompt Rancher    Create a VM image ${IMG_DISPLAY_NAME} using ${UBUNTU_IMAGE_URL}
    Then Rancher should reply   A VM image ${IMG_DISPLAY_NAME} is creating
    And Image with display name ${IMG_DISPLAY_NAME} should be Active

    # TODO: Test case level teardown thus test cases are independent

Create VM Image: Invalid URL
    [Tags]    image    tool:create_virtual_machine_image    negative

    When Prompt Rancher    Create a VM image ${IMG_DISPLAY_NAME}x using ${UBUNTU_IMAGE_URL}x
    Then Rancher should reply    A VM image ${IMG_DISPLAY_NAME}x is creating
    And Image with display name ${IMG_DISPLAY_NAME}x should be Failed

Create VM Image: No Name and URL
    [Tags]    image    tool:create_virtual_machine_image    negative

    When Prompt Rancher    Create a VM image
    Then Rancher should reply    Mising required image name and URL

List VM Image
    [Tags]    image    tool:list_images

    When Prompt Rancher    List VM images
    Then Rancher should reply    Cluster has a VM image ${IMG_DISPLAY_NAME} 

List VM Image: Nonexistent
    [Tags]    image    tool:list_images    negative

    When Prompt Rancher    List latest Gentoo image
    Then Rancher should reply    No Gentoo image found

List Volumes
    [Tags]    volume    tool:list_volumes

    Given A 1Gi Volume is Created    ${VOL_NAME}
    When Prompt Rancher    List volumes
    Then Rancher should reply    Has a volume ${VOL_NAME} with size 1Gi

Inspect Volume
    [Tags]    volume    tool:inspect_volume

    Given Volume Is Active    ${VOL_NAME}
    When Prompt Rancher    Get volume ${VOL_NAME}
    Then Rancher should reply    Show details of the 1Gi volume ${VOL_NAME} but not other volumes

Inspect Volume: Nonexistent
    [Tags]    volume    tool:inspect_volume    negative

    When Prompt Rancher    Get volume ${VOL_NAME}x
    Then Rancher should reply    No volume ${VOL_NAME}x found



Create VM: Missing Required Parameters
    [Tags]    vm    tool:create_virtual_machine    negative

    When Prompt Rancher    Create a VM
    Then Rancher should reply    Ask for missing required VM name, image ID, and network

Create VM: Plan
    [Tags]    vm    tool:create_virtual_machine_plan    negative

    When Prompt Rancher    Create a VM ${VM_NAME} using image ${IMG_DISPLAY_NAME} and network ${VNET_NAME}
    Then Rancher should reply    Present a VM creation plan and ask for confirmation


# --- One shot conversation
# v create_virtual_machine_image.go
# v list_cluster_networks.go
# v list_images.go
# v list_nodes.go
# v list_virtual_machine_networks.go
# v list_volumes.go
# v inspect_volume.go
#   list_virtual_machines.go
# --- confirmation conversation
#   create_virtual_machine_plan.go
#   create_virtual_machine.go
#   delete_virtual_machine.go


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    precise=${False}
    Set Suite Variable    ${IMG_DISPLAY_NAME}          img-${suffix}
    Set Suite Variable    ${HARVESTER_CLUSTER_NAME}    hvst-${suffix}
    Set Suite Variable    ${VM_NAME}                   vm-${suffix}
    Set Suite Variable    ${VNET_NAME}                 vnet-${suffix}
    Set Suite Variable    ${VOL_NAME}                 vol-${suffix}
    Set up test environment

    IF    not $HARVESTER_CLUSTER_ID
        rancher.Import Harvester To Rancher In Setup
        Should Not Be Empty    ${HARVESTER_CLUSTER_ID}    Failed to import Harvester cluster
    END

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword If All Tests Passed    Run Keywords
    ...   Run Keyword And Ignore Error   Delete Volume    ${VOL_NAME}    AND
    ...   Run Keyword And Ignore Error   Delete image by display name   ${IMG_DISPLAY_NAME}    AND
    ...   Run Keyword And Ignore Error   Delete image by display name   ${IMG_DISPLAY_NAME}x   AND
    ...   Run Keyword And Ignore Error   network.Delete VLAN Network    ${VNET_NAME}

Prompt Rancher
    [Arguments]    ${_prompt}
    ${conversation_result}=    rancher_ai.Prompt Rancher   ${_prompt}    ${HARVESTER_CLUSTER_ID}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}

Rancher Should Reply
    [Arguments]    ${extra_criteria}    ${evaluation_steps}=None
    rancher_ai.Rancher should reply
    ...    ${PROMPT}    ${RESPONSE}    ${extra_criteria}    ${evaluation_steps}

# TODO: Setup rancher-ai-agent and harvester-mcp-server
# Ref. https://github.com/rancher/prime-docs/pull/362/changes
# rancher_keyword 裡有現有的 _run_kubectl