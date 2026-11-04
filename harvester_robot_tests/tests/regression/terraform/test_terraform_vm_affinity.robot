*** Settings ***
Documentation    VM affinity through the terraform provider
...    harvester_virtualmachine node_affinity and pod_anti_affinity
...    (terraform-provider-harvester#154, harvester/harvester#9936): the VMs
...    must land where the rules say, and a plan right after the apply must
...    be empty. Needs a provider release with these blocks (v1.10.0 or
...    later, see TF_PROVIDER_VERSION) and at least two nodes.
Test Tags        terraform    regression

Resource    ../../../keywords/variables.resource
Resource    ../../../keywords/common.resource
Resource    ../../../keywords/host.resource
Resource    ../../../keywords/image.resource
Resource    ../../../keywords/virtualmachine.resource
Resource    ../../../keywords/terraform.resource

Suite Setup       Local Suite Setup
Suite Teardown    Local Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${AFFINITY_LABEL}    harvesterhci.io/test-tf-affinity
# Dynamic Variables
${SUFFIX}            ${EMPTY}
${IMG_NAME}          ${EMPTY}
${LABELLED_NODE}     ${EMPTY}


*** Test Cases ***
VM With Required Node Affinity Runs On The Labelled Node
    [Tags]    p0
    [Documentation]    A VM that requires a node label runs on the only node
    ...    carrying it.
    ${vm}=    Set Variable    vm-node-${SUFFIX}
    Given Terraform workspace is initialized    node-affinity
    And Terraform VM is defined    node-affinity    ${vm}    ${IMG_NAME}
    And Terraform VM requires node label    node-affinity    ${vm}    ${AFFINITY_LABEL}    ${SUFFIX}
    When Terraform configuration is applied    node-affinity
    Then VM should be running    ${vm}
    And VM should be running on node    ${vm}    ${LABELLED_NODE}
    And Terraform plan should have no changes    node-affinity

VMs With Required Pod Anti-Affinity Run On Different Nodes
    [Tags]    p0
    [Documentation]    Two VMs that must not share a node run on two nodes.
    ${vm_a}=    Set Variable    vm-anti-a-${SUFFIX}
    ${vm_b}=    Set Variable    vm-anti-b-${SUFFIX}
    Given Terraform workspace is initialized    anti-affinity
    And Terraform VM is defined    anti-affinity    ${vm_a}    ${IMG_NAME}
    And Terraform VM is defined    anti-affinity    ${vm_b}    ${IMG_NAME}
    And Terraform VM avoids VMs    anti-affinity    ${vm_a}    ${vm_b}
    And Terraform VM avoids VMs    anti-affinity    ${vm_b}    ${vm_a}
    When Terraform configuration is applied    anti-affinity
    Then VM should be running    ${vm_a}
    And VM should be running    ${vm_b}
    And VMs should run on different nodes    ${vm_a}    ${vm_b}
    And Terraform plan should have no changes    anti-affinity


*** Keywords ***
Local Suite Setup
    Set up test environment
    ${node_count}=    Get cluster node count
    Skip If    ${node_count} < 2    Needs at least two nodes, found ${node_count}
    ${suffix}=    Generate Unique Name
    Set Suite Variable    ${SUFFIX}      ${suffix}
    Set Suite Variable    ${IMG_NAME}    img-${suffix}
    Image is available for VM creation    ${IMG_NAME}    ${OPENSUSE_IMAGE_URL}
    # The last node, so the scheduler's first choice is less likely to match by chance
    ${last}=    Evaluate    ${node_count} - 1
    ${node}=    Get node ${last}
    Set Suite Variable    ${LABELLED_NODE}    ${node}
    Node label is added    ${LABELLED_NODE}    ${AFFINITY_LABEL}    ${SUFFIX}

Local Suite Teardown
    Run Keyword If    '${LABELLED_NODE}'    Run Keyword And Ignore Error
    ...    Node label is removed    ${LABELLED_NODE}    ${AFFINITY_LABEL}
    Run Keyword If All Tests Passed    Delete Suite Resources
    Run Keyword If Any Tests Failed    Log Variables

Delete Suite Resources
    Run Keyword And Ignore Error    Terraform workspace is destroyed    node-affinity
    Run Keyword And Ignore Error    Terraform workspace is destroyed    anti-affinity
    Run Keyword And Ignore Error    Delete image by name    ${IMG_NAME}
