*** Settings ***
Documentation    KubeOVN VPC NAT Gateway Test Cases

Test Tags        kubeovn vpc nat gateway regression

Resource         ../../../keywords/variables.resource
Resource         ../../../keywords/common.resource
Resource         ../../../keywords/addon.resource
Resource         ../../../keywords/kubeovn.resource

Suite Setup      Suite Setup For KubeOVN VPC NAT Gateway Tests
Suite Teardown   Suite Teardown For KubeOVN VPC NAT Gateway Tests

*** Variables ***
${ADDON_KUBEOVN}               kubeovn-operator
${DEFAULT_VPC_NAME}            ovn-cluster
${DEFAULT_SUBNET_NAME_JOIN}    join
${DEFAULT_SUBNET_NAME}         ovn-default

*** Test Cases ***
Test Default KubeOVN VPC Exists and Default subnets exist
    [Tags]    p0    coretest    kubeovn
    [Documentation]    Verify KubeOVN Default VPC Exists

    When KubeOVN Addon is Enabled    ${ADDON_KUBEOVN}
    Then KubeOVN VPC Should Exist    ${DEFAULT_VPC_NAME}
    Then KubeOVN Subnet Should Exist    ${DEFAULT_SUBNET_NAME_JOIN}
    Then KubeOVN Subnet Should Exist    ${DEFAULT_SUBNET_NAME}

*** Keywords ***
Suite Setup For KubeOVN VPC NAT Gateway Tests
    [Documentation]    Initialize test environment for KubeOVN VPC NAT Gateway tests
    Log    Setting up test environment for KubeOVN VPC NAT Gateway tests
    Set up test environment
    Log    Test environment ready

Suite Teardown For KubeOVN VPC NAT Gateway Tests
    [Documentation]    Clean up test environment for KubeOVN VPC NAT Gateway tests
    Log    Cleaning up up test environment for KubeOVN VPC NAT Gateway tests
    Cleanup test resources
    Log    Suite teardown completed
