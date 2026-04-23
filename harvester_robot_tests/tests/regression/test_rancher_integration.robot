*** Settings ***
Documentation    Rancher Integration Test Cases (RKE2)
...             This suite tests Rancher integration with Harvester for a given
...             RKE2 version. It covers cluster creation, workload deployment, scaling, and upgrade scenarios.

Resource         ../../keywords/rancher.resource

Suite Setup      Suite Setup For Rancher Integration Tests
Suite Teardown   Suite Teardown For Rancher Integration Tests

*** Test Cases ***
Test Create Single Node RKE2 Cluster with Basic Workloads
    [Tags]    smoke    rancher    rke2    p0    rwx
    [Documentation]    Create a single-node RKE2 cluster and verify basic workloads
    ...               (CSI, Whoami, LB DHCP, LB Pool) are functional.
    Given Single node RKE2 cluster is created
    Then Harvester deployments should be ready    ${SINGLE_CLUSTER_ID}
    When Basic workloads are deployed on single node cluster
    Then Basic workloads should be active on single node cluster

Test RWX Volume On Single Node Cluster
    [Tags]    rancher    rke2    p1    rwx
    [Documentation]    Enable storage network on the single-node cluster (requires
    ...               stopping and restarting the VM), create an RWX StorageClass,
    ...               PVC, and StatefulSet with 2 replicas, then verify data written
    ...               by one pod is readable from the other. Validates Harvester CSI
    ...               driver RWX volume support end-to-end including the storage
    ...               network lifecycle.
    Given Single node cluster is available
    And Storage network is enabled for RWX
    And Single node cluster should be ready
    And Basic workloads should be active on single node cluster
    When RWX volume is created on single node cluster
    And RWX StatefulSet with 2 replicas is deployed on single node cluster
    Then RWX StatefulSet should be ready on single node cluster
    And RWX shared data should be accessible across pods on single node cluster
    [Teardown]    Cleanup RWX test resources on single node cluster

Test Create Multi Node RKE2 Cluster
    [Tags]    rancher    rke2    p0
    [Documentation]    Create and verify a 3-node RKE2 cluster.
    When Multi node RKE2 cluster is created
    Then Harvester deployments should be ready    ${MULTI_CLUSTER_ID}

Test CSI Deployment
    [Tags]    rancher    rke2    p0
    [Documentation]    Deploy a CSI workload with PVC on the multi-node cluster.
    Given Multi node cluster is available
    When CSI workload with PVC is deployed
    Then CSI deployment and PVC should be active

Test Whoami Deployment
    [Tags]    rancher    rke2    p0
    [Documentation]    Deploy a Whoami workload on the multi-node cluster.
    Given Multi node cluster is available
    When Whoami workload is deployed
    Then Whoami deployment should be active

Test Load Balancer DHCP Mode
    [Tags]    rancher    rke2    p0
    [Documentation]    Create and verify a LoadBalancer service in DHCP mode.
    Given Multi node cluster is available
    When Load balancer is created in DHCP mode
    Then DHCP load balancer should be serving traffic

Test Load Balancer Pool Mode
    [Tags]    rancher    rke2    p0
    [Documentation]    Create and verify a LoadBalancer service in IP Pool mode.
    Given Multi node cluster is available
    When Load balancer is created in pool mode
    Then Pool load balancer should be serving traffic

Test Scale Up RKE2 Cluster
    [Tags]    rancher    rke2    p0
    [Documentation]    Scale up the multi-node cluster by adding a worker node.
    Given Multi node cluster is available
    When Worker pool with 1 node is added
    Then Multi node cluster should be ready

Test Verify Workloads After Scale Up
    [Tags]    rancher    rke2    p0
    [Documentation]    Verify existing workloads and Harvester deployments still running after scale up.
    Given Multi node cluster is available
    Then All existing workloads should be active

Test New Workloads After Scale Up
    [Tags]    rancher    rke2    p0
    [Documentation]    Create new CSI workload after scale up to verify cluster health.
    Given Multi node cluster is available
    When New CSI workload is deployed    scaleup
    Then New CSI workload should be active    scaleup
    And Harvester deployments should be ready    ${MULTI_CLUSTER_ID}
    [Teardown]    Cleanup temporary workloads    scaleup

Test Scale Down RKE2 Cluster
    [Tags]    rancher    rke2    p0
    [Documentation]    Scale down the multi-node cluster by removing the worker pool.
    Given Multi node cluster is available
    When Worker pool is removed
    Then Multi node cluster should be ready

Test Upgrade RKE2 Cluster
    [Tags]    rancher    rke2    p1
    [Documentation]    Upgrade the multi-node RKE2 cluster to the next available
    ...               patch version, verify workloads survive, scale up, and create
    ...               new workloads on the upgraded cluster.
    Given Multi node cluster is available
    And Next RKE2 version is available
    When Multi node cluster is upgraded to next version
    Then Multi node cluster should be ready
    And All existing workloads should be active
    When Worker pool with 1 node is added
    Then Multi node cluster should be ready
    When New CSI workload is deployed    upgrade
    Then New CSI workload should be active    upgrade
    And Harvester deployments should be ready    ${MULTI_CLUSTER_ID}
    [Teardown]    Cleanup upgrade test resources

Test Cleanup Workloads
    [Tags]    rancher    rke2    p0
    [Documentation]    Delete all workloads from the multi-node cluster.
    Given Multi node cluster is available
    When All test workloads are removed from cluster
    Then Workloads should be cleaned up

Test Delete RKE2 Clusters
    [Tags]    rancher    rke2    p0
    [Documentation]    Delete both single-node and multi-node clusters.
    When Single node RKE2 cluster is deleted
    And Multi node RKE2 cluster is deleted
    Then Clusters should be deleted

Test Create Single Node Custom RKE2 Cluster with Basic Workloads
    [Tags]     rancher    rke2    custom    p2
    [Documentation]    Create a single-node custom RKE2 cluster with Harvester
    ...               cloud provider and verify basic workloads (CSI, Whoami, LB)
    ...               are functional. Unlike the node driver cluster, nodes are
    ...               registered via cloud-init with the Rancher registration command.
    Given Single node custom RKE2 cluster is created
    Then Harvester deployments should be ready    ${CUSTOM_CLUSTER_ID}
    When Basic workloads are deployed on single node custom cluster
    Then Basic workloads should be active on single node custom cluster
    [Teardown]    Cleanup custom cluster test resources

Test Import Existing RKE2 Cluster with Basic Workloads
    [Tags]     rancher    rke2    import    p2    chart
    [Documentation]    Deploy RKE2 on a Harvester VM via cloud-init, import
    ...               the existing cluster into Rancher, install Harvester
    ...               Cloud Provider and CSI Driver via Rancher Apps, and
    ...               verify basic workloads (CSI, Whoami) are functional.
    Given Single node import RKE2 cluster is created
    Then Harvester CSI driver should be ready    ${IMPORT_CLUSTER_ID}
    When Basic workloads are deployed on single node import cluster
    Then Basic workloads should be active on single node import cluster
    [Teardown]    Cleanup import cluster test resources
