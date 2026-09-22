*** Settings ***
Documentation    KubeOVN Keywords - Reusable keywords for KubeOVN operations
Library          ../libs/keywords/kubeovn_vpc_keywords.py
Library          ../libs/keywords/kubeovn_subnet_keywords.py
Library          ../libs/keywords/kubeovn_vpc_nat_gateway_keywords.py
Library          Process
Resource         variables.resource
Resource         common.resource
Resource         addon.resource

*** Keywords ***

### KubeOVN Addon Keywords ###
#

Initial KubeOVN Addon State Is Captured
    [Arguments]    ${addon_name}
    [Documentation]    Capture and store initial state of the addon
    ${initial_state}=    addon.Get Initial State    ${addon_name}
    Set Suite Variable    ${INITIAL_STATE_KUBEOVN}    ${initial_state}
    Log    Captured initial addon state: ${initial_state}

KubeOVN Addon Is Enabled
    [Arguments]    ${addon_name}
    [Documentation]    Enable the KubeOVN addon and wait for deployment
    ${is_enabled}=    addon.Is Enabled    ${addon_name}
    Run Keyword If    not ${is_enabled}    addon.Enable    ${addon_name}
    addon.Wait For Enabled    ${addon_name}    timeout=900
    Log    KubeOVN addon ${addon_name} is enabled

### KubeOVN VPC Keywords ###
#

Create KubeOVN VPC
    [Arguments]    ${vpc_name}    &{kwargs}
    [Documentation]    Create a KubeOVN VPC
    kubeovn_vpc_keywords.Create VPC    ${vpc_name}    &{kwargs}

Delete KubeOVN VPC
    [Arguments]    ${vpc_name}
    [Documentation]    Delete KubeOVN VPC
    kubeovn_vpc_keywords.Delete VPC    ${vpc_name}

KubeOVN VPC Should Exist
    [Arguments]    ${vpc_name}
    [Documentation]    Check hat the KubeOVN VPC vpc_name exists
    ${vpc}=    kubeovn_vpc_keywords.Get VPC    ${vpc_name}
    Should Not Be Empty    ${vpc}

KubeOVN VPC Should Not Exist
    [Arguments]    ${vpc_name}
    [Documentation]    Check hat the KubeOVN VPC vpc_name does not exist
    ${vpc}=    kubeovn_vpc_keywords.Get VPC    ${vpc_name}
    Should Be Empty    ${vpc}

KubeOVN VPC is Created
    [Arguments]    ${name}    &{kwargs}
    [Documentation]    Create KubeOVN VPC
    ${vpc}=    kubeovn_vpc_keywords.Get VPC    ${name}
    Run Keyword If    ${vpc} is None
    ...    Create KubeOVN VPC    ${name}    &{kwargs}

KubeOVN VPC is Deleted
    [Arguments]    ${name}
    [Documentation]    Delete KubeOVN VPC
    ${vpc}=    kubeovn_vpc_keywords.Get VPC    ${name}
    Run Keyword If    ${vpc} is not None
    ...    Delete KubeOVN VPC    ${name}

KubeOVN VPC Should be Active
    [Arguments]    ${vpc_name}
    [Documentation]    Check that the KubeOVN VPC vpc_name is active
    ${vpc_status}=    kubeovn_vpc_keywords.Get VPC Status   ${vpc_name}
    Should Be True    ${vpc_status}

### KubeOVN Subnet Keywords ###
#

Create KubeOVN Subnet
    [Arguments]    ${subnet_name}    &{kwargs}
    [Documentation]    Create KubeOVN Subnet
    kubeovn_subnet_keywords.Create Subnet    ${subnet_name}    &{kwargs}

Delete KubeOVN Subnet
    [Arguments]    ${name}
    [Documentation]    Delete KubeOVN Subnet
    kubeovn_subnet_keywords.Delete Subnet    ${name}

KubeOVN Subnet Should Exist
    [Arguments]    ${subnet_name}
    [Documentation]    Check hat the KubeOVN Subnet subnet_name exists
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${subnet_name}
    Should Not Be Empty    ${subnet}

KubeOVN Subnet Should Not Exist
    [Arguments]    ${subnet_name}
    [Documentation]    Check hat the KubeOVN Subnet subnet_name does not exist
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${subnet_name}
    Should Be Empty    ${subnet}

KubeOVN Subnet is Created
    [Arguments]    ${name}    &{kwargs}
    [Documentation]    Create KubeOVN Subnet
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${name}
    Run Keyword If    ${subnet} is None
    ...    Create KubeOVN Subnet    ${name}    &{kwargs}

KubeOVN Subnet is Deleted
    [Arguments]    ${name}
    [Documentation]    Delete KubeOVN Subnet
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${name}
    Run Keyword If    ${subnet} is not None
    ...    Delete KubeOVN Subnet    ${name}

KubeOVN Subnet Should Have VPC
    [Arguments]    ${subnet_name}    ${vpc_name}
    [Documentation]    Check hat the KubeOVN Subnet is in the specified VPC
    ${subnet}=    kubeovn_subnet_keywords.Get Subnet    ${subnet_name}
    Should Be Equal    ${subnet['spec']['subnet']}    ${vpc_name}

### KubeOVN VPC NAT Gateway Keywords ###
#

Create KubeOVN VPC NAT Gateway
    [Arguments]    ${name}    &{kwargs}
    [Documentation]    Create a KubeOVN VPC NAT Gateway
    kubeovn_vpc_nat_gateway_keywords.Create VPC NAT Gateway    ${name}    &{kwargs}

Delete KubeOVN VPC NAT Gateway
    [Arguments]    ${name}    &{kwargs}
    [Documentation]    Delete a KubeOVN VPC NAT Gateway
    kubeovn_vpc_nat_gateway_keywords.Delete VPC NAT Gateway    ${name}    &{kwargs}

KubeOVN VPC NAT Gateway is Created
    [Arguments]    ${name}    &{kwargs}
    [Documentation]    Ensure the KubeOVN VPC NAT Gateway Exists
    ${gateway}=    kubeovn_vpc_nat_gateway_keywords.Get VPC NAT Gateway    ${name}
    Run Keyword If    ${gateway} is None
    ...    Create KubeOVN VPC NAT Gateway    ${name}    &{kwargs}

KubeOVN VPC NAT Gateway is Deleted
    [Arguments]    ${name}
    [Documentation]    Ensure the KubeOVN VPC NAT Gateway is deleted
    ${gateway}=    kubeovn_vpc_nat_gateway_keywords.Get VPC NAT Gateway    ${name}
    Run Keyword If    ${gateway} is not None
    ...    Delete KubeOVN VPC NAT Gateway    ${name}
