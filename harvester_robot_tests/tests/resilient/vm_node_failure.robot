*** Settings ***
Documentation     VM Node Failure Negative Test Cases
Test Tags         negative    ha    node-failure
Resource          ../../keywords/variables.resource
Resource          ../../keywords/common.resource
Resource          ../../keywords/virtualmachine.resource
Resource          ../../keywords/host.resource
Resource          ../../keywords/image.resource
Test Setup        Set up test environment
Test Teardown     Cleanup test resources and restore nodes

*** Test Cases ***
Test VM Survives Node Reboot
    [Tags]    p0    node-reboot
    [Documentation]    Verify VM migrates when node is rebooted
    ...    1. Create VM on node 0
    ...    2. Write data to VM
    ...    3. Reboot node 0
    ...    4. Verify VM migrates to another node
    ...    5. Verify data integrity
    Given Cluster has at least 3 nodes
    And Create image from url    0    ${UBUNTU_IMAGE_URL}
    And Create VM    0    cpu=2    memory=4Gi    numberOfReplicas=3
    And Attach VM To Node    0    0
    And Wait for VM Running    0
    When Write Data To VM    0
    And Reboot Node    0
    Then Wait for VM Migration To Node Completed    0    different
    And Wait for VM Running    0
    And Check VM Data Is Intact    0
    And Wait For Node Ready    0

Test VM HA During Node Power Off
    [Tags]    p0    node-down
    [Documentation]    Verify VM HA when node loses power
    Given Cluster has at least 3 nodes
    And Create image from url    0    ${UBUNTU_IMAGE_URL}
    And Create VM    0    cpu=2    memory=4Gi    numberOfReplicas=3
    And Attach VM To Node    0    0
    And Wait for VM Running    0
    When Write Data To VM    0
    And Power Off Node    0
    Then Wait For Node To Be Marked As Down    0
    And Wait for VM Migration To Node Completed    0    different    timeout=300
    And Wait for VM Running    0
    And Check VM Data Is Intact    0