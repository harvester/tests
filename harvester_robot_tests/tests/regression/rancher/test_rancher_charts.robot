*** Settings ***
Documentation    Rancher Chart Integration Test Cases (RKE2)
...             Covers importing an existing RKE2 cluster into Rancher and testing
...             the Harvester CSI Driver and Cloud Provider charts from Rancher Apps.
Test Tags        rancher    rke2    regression
Resource         ../../../keywords/rancher.resource

Suite Setup      Get Or Create Rancher Test Environment
Suite Teardown   Teardown Rancher Test Suite    cleanup_import_cluster=${True}

*** Test Cases ***
Test Import Existing RKE2 Cluster
    [Tags]     import    chart    p2    csi    cloudprovider
    [Documentation]    Deploy RKE2 on a Harvester VM via cloud-init and import the
    ...               existing cluster into Rancher.
    When Single node import RKE2 cluster is created
    Then Import cluster should be ready and running

Test Upgrade Harvester CSI Driver Chart On Imported RKE2 Cluster
    [Tags]     import    chart    csi    upgrade    p2
    [Documentation]   Test CSI chart upgrade from Rancher Apps from n-1 to latest

    Given Import cluster should be ready
    And Multiple Harvester CSI driver chart versions are available

    When Harvester CSI driver chart is installed on single node import cluster    ${CSI_PREV_VERSION}
    And CSI workload is deployed on single node import cluster
    Then CSI workload should be active on single node import cluster

    When Harvester CSI driver chart is upgraded to latest on import cluster
    Then Harvester CSI driver should be ready    ${IMPORT_CLUSTER_ID}

    When CSI upgrade workload is restarted on import cluster
    Then CSI workload should be active on single node import cluster

    When New CSI workload is deployed    csiup    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}
    Then New CSI workload should be active    csiup    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}

    [Teardown]    Cleanup CSI upgrade test resources on import cluster

Test Harvester CSI Driver Chart On Imported RKE2 Cluster
    [Tags]     import    chart    csi    p2
    [Documentation]    Tests the Harvester CSI Driver chart from Rancher Apps
    Given Import cluster should be ready
    When Harvester CSI driver chart is installed on single node import cluster
    Then Harvester CSI driver should be ready    ${IMPORT_CLUSTER_ID}
    When CSI workload is deployed on single node import cluster
    Then CSI workload should be active on single node import cluster

Test Upgrade Harvester Cloud Provider Chart On Imported RKE2 Cluster
    [Tags]     import    chart    cloudprovider    upgrade    p2
    [Documentation]    Test cloud provider chart upgrade from Rancher Apps from n-1 to latest

    Given Import cluster should be ready
    And Multiple Harvester cloud provider chart versions are available

    When Harvester cloud provider chart is installed on single node import cluster    ${CP_PREV_VERSION}
    And Cloud provider workloads are deployed on single node import cluster
    Then Cloud provider workloads should be active on single node import cluster

    When Harvester cloud provider chart is upgraded to latest on import cluster
    Then Harvester cloud provider should be ready    ${IMPORT_CLUSTER_ID}

    When Cloud provider upgrade workload is restarted on import cluster
    Then Cloud provider workloads should be active on single node import cluster

    When Cloud provider workloads are deployed on single node import cluster    cpup2
    Then Cloud provider workloads should be active on single node import cluster    cpup2

    [Teardown]    Cleanup cloud provider upgrade test resources on import cluster

Test Harvester Cloud Provider Chart On Imported RKE2 Cluster
    [Tags]     import    chart    cloudprovider    p2
    [Documentation]    Tests the Harvester Cloud Provider chart from Rancher Apps
    Given Import cluster should be ready
    When Harvester cloud provider chart is installed on single node import cluster
    Then Harvester cloud provider should be ready    ${IMPORT_CLUSTER_ID}
    When Cloud provider workloads are deployed on single node import cluster
    Then Cloud provider workloads should be active on single node import cluster
