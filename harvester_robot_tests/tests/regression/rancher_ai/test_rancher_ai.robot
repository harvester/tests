*** Settings ***
Documentation    Evaluate image import initiation followed by an independent image listing.
Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/rancher.resource
Resource    ../../../keywords/rancher_ai.resource
Resource    ../../../keywords/host.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown
Test Tags        rancher-ai


*** Variables ***
${HARVESTER_CLUSTER_NAME}    ${EMPTY}
${HARVESTER_CLUSTER_ID}      ${EMPTY}
${PROMPT}              ${EMPTY}
${RESPONSE}            ${EMPTY}
${IMG_DISPLAY_NAME}    ${EMPTY}
${IMG_NAME}            ${EMPTY}
${VM_NAME}             ${EMPTY}
${VM_VOL_NAMES}        ${EMPTY}
${VNET_NAME}           ${EMPTY}
${VOL_NAME}            ${EMPTY}


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
    Then Rancher should reply   A VM image ${IMG_DISPLAY_NAME} is creating/importing
    And Image with display name ${IMG_DISPLAY_NAME} should be Active
    
    ${IMG_NAME}=    Get Image Name By Display Name    ${IMG_DISPLAY_NAME}
    Set Suite Variable    ${IMG_NAME}

Create VM Image: No Name and URL
    [Tags]    image    tool:create_virtual_machine_image    negative
    When Prompt Rancher    Create a VM image
    Then Rancher should reply
    ...    The required image name is missing, along with some help text.

List VM Image
    [Tags]    image    tool:list_images
    When Prompt Rancher    List VM images
    Then Rancher should reply    Cluster has a VM image ${IMG_NAME} 

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
    When Prompt Rancher    Get volume img-xxx
    Then Rancher should reply    No volume img-xxx found, along with some help text.

Create VM: Missing Required Parameters
    [Tags]    vm    tool:create_virtual_machine    negative
    When Prompt Rancher    Create a VM
    Then Rancher should reply
    ...    Missing required parameters, along with some help text.

Create VM: Plan
    [Tags]    vm    tool:create_virtual_machine_plan
    When Prompt Rancher
    ...    Create a VM ${VM_NAME} using image ${IMG_NAME} and network ${VNET_NAME}
    Then Rancher should reply    A confirmation response with a VM resource
    And VM does not exist   ${VM_NAME}

Create VM
    [Tags]    vm    tool:create_virtual_machine
    When Prompt Rancher And Confirm
    ...    Create a VM ${VM_NAME} using image ${IMG_NAME} and network ${VNET_NAME}
    Then Rancher should reply    VM ${VM_NAME} is created
    And VM should be running    ${VM_NAME}

    ${volumes}=    Get VM Volumes    ${VM_NAME}
    Set Suite Variable    ${VM_VOL_NAMES}    ${volumes}

List VM
    [Tags]    vm    tool:list_virtual_machines
    When Prompt Rancher    List VMs
    Then Rancher should reply    Should contain VM ${VM_NAME}

Delete VM: Plan
    [Tags]    vm    tool:delete_virtual_machine_plan
    When Prompt Rancher    Delete VM ${VM_NAME}
    Then Rancher should reply    A confirmation response with a VM resource
    And VM should be running    ${VM_NAME}

Delete VM
    [Tags]    vm    tool:delete_virtual_machine    tool:list_virtual_machines
    When Prompt Rancher And Confirm    Delete VM ${VM_NAME}
    Then Rancher should reply    VM ${VM_NAME} is deleted
    And VM should be deleted   ${VM_NAME}
    And Prompt Rancher    Get VM ${VM_NAME}
    And Rancher should reply    No VM ${VM_NAME} found, along with some help text.


*** Keywords ***
Local Suite Setup
    ${suffix}=    Generate Unique Name    precise=${False}
    Set Suite Variable    ${HARVESTER_CLUSTER_NAME}    hvst-${suffix}
    Set Suite Variable    ${IMG_DISPLAY_NAME}          img-${suffix}
    Set Suite Variable    ${VM_NAME}                   vm-${suffix}
    Set Suite Variable    ${VNET_NAME}                 vnet-${suffix}
    Set Suite Variable    ${VOL_NAME}                  vol-${suffix}
    Set up test environment

    IF    not $HARVESTER_CLUSTER_ID
        rancher.Import Harvester To Rancher In Setup
        Should Not Be Empty    ${HARVESTER_CLUSTER_ID}    Failed to import Harvester cluster
    END
    rancher_ai.Wait For Rancher AI Deployments Ready

Local Suite Teardown
    Run Keyword If Any Tests Failed    Log Variables
    Run Keyword If All Tests Passed    Run Keywords
    ...    Run Keyword And Ignore Error   VM is deleted    ${VM_NAME}    AND
    ...    Run Keyword And Ignore Error   Delete Volume    ${VOL_NAME}    AND
    ...    Run Keyword And Ignore Error   Delete Volumes Concurrently    ${VM_VOL_NAMES}    AND
    ...    Run Keyword And Ignore Error   Delete image by display name    ${IMG_DISPLAY_NAME}    AND
    ...    Run Keyword And Ignore Error   Delete image by display name    ${IMG_DISPLAY_NAME}x    AND
    ...    Run Keyword And Ignore Error   network.Delete VLAN Network    ${VNET_NAME}    AND
    ...    Run Keyword And Ignore Error   Delete Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}

Prompt Rancher
    [Arguments]    ${_prompt}
    ${conversation_result}=    rancher_ai.Prompt Rancher   ${_prompt}    ${HARVESTER_CLUSTER_ID}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}

Prompt Rancher And Confirm
    [Arguments]    ${_prompt}
    ${conversation_result}=    rancher_ai.Prompt Rancher And Confirm   ${_prompt}    ${HARVESTER_CLUSTER_ID}
    Set Test Variable    ${PROMPT}    ${_prompt}
    Set Test Variable    ${RESPONSE}    ${conversation_result.answer}

Rancher Should Reply
    [Arguments]    ${extra_criteria}    ${evaluation_steps}=None
    rancher_ai.Rancher should reply
    ...    ${PROMPT}    ${RESPONSE}    ${extra_criteria}    ${evaluation_steps}
