*** Settings ***

Documentation    KubeOVN VPC NAT Gateway Test Cases

Test Tags        kubeovn vpc nat gateway regression

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/addon.resource
Resource         ../../../keywords/kubeovn.resource
Resource         ../../../keywords/cni.resource

Suite Setup      Local Suite Setup
Suite Teardown   Local Suite Teardown

Test Teardown     Common Test Teardown

*** Variables ***

${ADDON_KUBEOVN}                   kubeovn-operator
${DEFAULT_VPC_NAME}                ovn-cluster
${DEFAULT_SUBNET_NAME_JOIN}        join
${DEFAULT_SUBNET_NAME}             ovn-default
${KUBEOVN_VPC_NAME}                ovn-test-vpc

${INTERNAL_NETWORK_NAME}           vswitchinternal
${EXTERNAL_NETWORK_NAME}           vswitchexternal
${INTERNAL_SUBNET_NAME}            subnetinternal
${EXTERNAL_SUBNET_NAME}            subnetexternal

${KUBEOVN_VPC_NAT_GATEWAY_NAME}    ovn-nat-gateway

*** Test Cases ***

Test Default KubeOVN VPC Exists and Default subnets exist
    [Tags]    p0    coretest    kubeovn
    [Documentation]    Verify KubeOVN Default VPC Exists

    When KubeOVN Addon is Enabled      ${ADDON_KUBEOVN}
    Then KubeOVN VPC Should Exist      ${DEFAULT_VPC_NAME}
    And KubeOVN Subnet Should Exist    ${DEFAULT_SUBNET_NAME_JOIN}
    And KubeOVN Subnet Should Exist    ${DEFAULT_SUBNET_NAME}

Test Creating a KubeOVN VPC with a NAT Gateway
    [Tags]    p0    coretest    kubeovn
    [Documentation]    Verify that a new KubeOVN VPC can be created
    ...    and a NAT gateway can be configured
    ...    Steps:
    ...      1) Create a tenant/internal network
    ...      2) Create an external network
    ...      3) Create a VPC
    ...      4) Create a Subnet in the VPC for the internal network
    ...      5) Create a Subnet in the VPC for the external network
    ...      6) Create a NAT Gateway config
    ...      7) Verify the NAT Gateway StatefulSet/Pod status

    When NetworkAttachmentDefinition is Created
    ...     ${DEFAULT_NAMESPACE}
    ...     ${INTERNAL_NETWORK_NAME}
    ...     nad_type=OverlayNetwork
    ...     provider=${INTERNAL_NETWORK_NAME}.${DEFAULT_NAMESPACE}.ovn
    And NetworkAttachmentDefinition is Created
    ...     ${KUBE_SYSTEM_NAMESPACE}
    ...     ${EXTERNAL_NETWORK_NAME}
    ...     nad_type=OverlayNetwork
    ...     master=ens9
    ...     provider=${EXTERNAL_NETWORK_NAME}.${KUBE_SYSTEM_NAMESPACE}.ovn
    And KubeOVN VPC is Created
    ...     ${KUBEOVN_VPC_NAME}
    And KubeOVN Subnet is Created
    ...     ${INTERNAL_SUBNET_NAME}
    ...     vpc=${KUBEOVN_VPC_NAME}
    ...     cidr_block=10.55.0.0/16
    ...     provider=${INTERNAL_NETWORK_NAME}.${DEFAULT_NAMESPACE}.ovn
    And KubeOVN Subnet is Created
    ...     ${EXTERNAL_SUBNET_NAME}
    ...     vpc=${KUBEOVN_VPC_NAME}
    ...     cidr_block=10.155.0.0/16
    ...     provider=${EXTERNAL_NETWORK_NAME}.${KUBE_SYSTEM_NAMESPACE}.ovn

    ${external_subnets}=    Create List    ${EXTERNAL_SUBNET_NAME}

    And KubeOVN VPC NAT Gateway is Created
    ...     ${KUBEOVN_VPC_NAT_GATEWAY_NAME}
    ...     vpc=${KUBEOVN_VPC_NAME}
    ...     lan_ip=10.55.0.254
    ...     internal_subnet=${INTERNAL_SUBNET_NAME}
    ...     external_subnets=${external_subnets}

    ${gateway_pods}=    common.Count Pods By Label
    ...     ${KUBE_SYSTEM_NAMESPACE}
    ...     app=vpc-nat-gw-${KUBEOVN_VPC_NAT_GATEWAY_NAME}
    ...     status=Running
    Then Should Be Equal As Integers    ${gateway_pods}    1

*** Keywords ***

Local Suite Setup
    [Documentation]    Initialize test environment for KubeOVN VPC NAT Gateway tests
    Log    Setting up test environment for KubeOVN VPC NAT Gateway tests
    Set up test environment
    Log    Test environment ready

Local Suite Teardown
    [Documentation]    Clean up test environment for KubeOVN VPC NAT Gateway tests
    Log    Cleaning up up test environment for KubeOVN VPC NAT Gateway tests
    Run Keyword If All Tests Passed    Cleanup VPC NAT Gateway
    Run Keyword If Any Tests Failed    Log Variables
    Log    Suite teardown completed

Cleanup VPC NAT Gateway
    Run Keyword And Ignore Error    KubeOVN VPC NAT Gateway is Deleted    ${KUBEOVN_VPC_NAT_GATEWAY_NAME}
    Run Keyword And Ignore Error    KubeOVN Subnet is Deleted             ${EXTERNAL_SUBNET_NAME}
    Run Keyword And Ignore Error    KubeOVN Subnet is Deleted             ${INTERNAL_SUBNET_NAME}
    Run Keyword And Ignore Error    KubeOVN VPC is Deleted                ${KUBEOVN_VPC_NAME}
    Run Keyword And Ignore Error    NetworkAttachmentDefinition is Deleted
    ...    ${KUBE_SYSTEM_NAMESPACE}    ${EXTERNAL_NETWORK_NAME}
    Run Keyword And Ignore Error    NetworkAttachmentDefinition is Deleted
    ...    ${DEFAULT_NAMESPACE}    ${INTERNAL_NETWORK_NAME}

Configure VPC NAT Gateway
    Log    Configuring VPC NAT Gateway
