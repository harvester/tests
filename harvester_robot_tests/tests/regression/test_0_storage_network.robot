*** Settings ***
Documentation    Storage Network Test Cases
Test Tags        storage    network    setting

Resource         ../../keywords/common.resource
Resource         ../../keywords/network.resource
Resource         ../../keywords/storage_network.resource

Suite Setup       Local Suite Setup
Suite Teardown    Common Suite Teardown
Test Teardown     Common Test Teardown


*** Variables ***
${CNET_NAME}    ${EMPTY}
${VNET_CIDR}    ${EMPTY}


*** Test Cases ***
Test Enable Storage Network
    [Tags]    p0    smoke
    Given Create Cluster Network    ${CNET_NAME}
    And Create VLAN Config    ${CNET_NAME}    ${CNET_NAME}    ${VLAN_NIC}
    And Get VLAN Network CIDR
    When storage_network.Enable    ${VLAN_ID}    ${CNET_NAME}    ${VNET_CIDR}
    Then storage_network.Wait For Enabled    ${VNET_CIDR}

Test Disable Storage Network
    [Tags]    p0    smoke
    Given storage_network.Is Enabled    ${VNET_CIDR}
    When storage_network.Disable
    Then storage_network.Wait For Disabled


*** Keywords ***
Local Suite Setup
    Set Up Test Environment
    # Cluster network names must stay short (the bridge interface name is
    # capped at 15 chars), so opt into the minute-precision short form.
    ${name}=    Generate Unique Name    qa    precise=${FALSE}
    Set Suite Variable    ${CNET_NAME}    ${name}

Get VLAN Network CIDR
    ${cidr}=    storage_network.Get VLAN Network CIDR    ${VLAN_ID}    ${CNET_NAME}
    Set Suite Variable    ${VNET_CIDR}    ${cidr}