*** Settings ***
Documentation    Longhorn V2 Data Engine Test Cases
Test Tags        longhorn    LHv2    LonghornV2    storage    experimental

Resource         ../../keywords/variables.resource
Resource         ../../keywords/setting.resource

Suite Setup       Local Suite Setup
Suite Teardown    Cleanup test resources


*** Variables ***
&{DATA_DISK_BY_NODE}    &{EMPTY}
${LHv2_SC_REPLICAS}    ${EMPTY}


*** Test Cases ***
Provision LHv2 Storages
    [Tags]    p1
    [Documentation]    Provision at most 3 storages with LHv2 Data Engine
    When Provision Storages With LHv2 Data Engine    &{DATA_DISK_BY_NODE}
    Then Wait Until LHv2 Storages Are Provisioned    &{DATA_DISK_BY_NODE}


*** Keywords ***
Local Suite Setup
    Given Set up test environment
    And storage.Cluster Has Available Data Disks And Set Suite Variables
    And setting.LHv2 Data Engine Is Disabled
    When setting.Enable LHv2 Data Engine
    Then setting.Wait Until LHv2 Data Engine Is Enabled
