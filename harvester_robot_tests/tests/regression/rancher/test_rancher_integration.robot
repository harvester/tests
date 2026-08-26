*** Settings ***
Documentation    Rancher Integration Test Cases (RKE2)
...             This suite tests Rancher integration with Harvester for a given
...             RKE2 version. It covers cluster creation, workload deployment, scaling, and upgrade scenarios.
Test Tags        rancher    rke2    regression
Resource         ../../../keywords/rancher.resource

Suite Setup      Suite Setup For Rancher Integration Tests
Suite Teardown   Suite Teardown For Rancher Integration Tests

*** Variables ***
${RBAC_CLUSTER_ID}              local
${RBAC_CHART_REPO_NAME}         rancher-charts
${RBAC_CHART_NAME}              harvester-rbac
${SUITE_CLUSTER_ID}             ${EMPTY}
${SUITE_PROJECT_ID}             ${EMPTY}
${RBAC_CHART_RELEASE_NAME}      harvester-rbac
${RBAC_CHART_NAMESPACE}         default
${HARVESTER_PROJECT_NAME}       ${EMPTY}
${HARVESTER_PROJECT_NAMESPACE}  rbactestns
${RBAC_CLUSTER_VIEW_USER}       virt-viewer
${RBAC_CLUSTER_MANAGE_USER}     virt-manager
${RBAC_PROJECT_VIEW_USER}       proj-viewer
${RBAC_PROJECT_MANAGE_USER}     proj-manager
${RBAC_CLUSTER_VIEW_ROLE}       virt-view-cluster
${RBAC_CLUSTER_MANAGE_ROLE}     virt-cluster-manage
${RBAC_PROJECT_VIEW_ROLE}       virt-project-view
${RBAC_PROJECT_MANAGE_ROLE}     virt-project-manage

*** Test Cases ***
# ──────────────────────────────────────────────────────────────────────────────
# TC1: Cluster Role – View Virtualization Resources
# ──────────────────────────────────────────────────────────────────────────────
Test TC1 - Assign Cluster View Role
    [Tags]    p0    rbac    cluster-role
    [Documentation]    Create '${RBAC_CLUSTER_VIEW_USER}', assign Standard User global role
    ...               and the virt-cluster-view cluster role on the Harvester cluster.
    Given RBAC test user does not exist    ${RBAC_CLUSTER_VIEW_USER}
    When RBAC test user is created    ${RBAC_CLUSTER_VIEW_USER}
    Then Standard User role is assigned to    ${RBAC_CLUSTER_VIEW_USER}
    And Cluster role is assigned to user    ${RBAC_CLUSTER_VIEW_USER}
    ...    ${SUITE_CLUSTER_ID}    ${RBAC_CLUSTER_VIEW_ROLE}

Test TC1 Verify - Cluster View Can Read VMs
    [Tags]    p0    rbac    cluster-role    verify
    [Documentation]    Confirm virt-viewer can GET VMs in 'default' namespace.
    Then User can read VMs in namespace    ${RBAC_CLUSTER_VIEW_USER}    default

Test TC1 Verify - Cluster View Cannot Write VMs
    [Tags]    p0    rbac    cluster-role    verify    negative
    [Documentation]    Confirm virt-viewer cannot CREATE VMs in 'default' namespace.
    Then User cannot write VMs in namespace    ${RBAC_CLUSTER_VIEW_USER}    default

# ──────────────────────────────────────────────────────────────────────────────
# TC2: Cluster Role – Manage Virtualization Resources
# ──────────────────────────────────────────────────────────────────────────────
Test TC2 - Assign Cluster Manage Role
    [Tags]    p0    rbac    cluster-role
    [Documentation]    Create '${RBAC_CLUSTER_MANAGE_USER}', assign Standard User global role
    ...               and the virt-cluster-manage cluster role on the Harvester cluster.
    Given RBAC test user does not exist    ${RBAC_CLUSTER_MANAGE_USER}
    When RBAC test user is created    ${RBAC_CLUSTER_MANAGE_USER}
    Then Standard User role is assigned to    ${RBAC_CLUSTER_MANAGE_USER}
    And Cluster role is assigned to user    ${RBAC_CLUSTER_MANAGE_USER}
    ...    ${SUITE_CLUSTER_ID}    ${RBAC_CLUSTER_MANAGE_ROLE}

Test TC2 Verify - Cluster Manage Can Read VMs
    [Tags]    p0    rbac    cluster-role    verify
    [Documentation]    Confirm virt-manager can GET VMs in 'default' namespace.
    Then User can read VMs in namespace    ${RBAC_CLUSTER_MANAGE_USER}    default

Test TC2 Verify - Cluster Manage Can Write VMs
    [Tags]    p0    rbac    cluster-role    verify
    [Documentation]    Confirm virt-manager can CREATE VMs in 'default' namespace.
    Then User can write VMs in namespace    ${RBAC_CLUSTER_MANAGE_USER}    default

# ──────────────────────────────────────────────────────────────────────────────
# TC3: Project Role – View Virtualization Resources
# ──────────────────────────────────────────────────────────────────────────────
Test TC3 - Assign Project View Role
    [Tags]    p0    rbac    project-role
    [Documentation]    Create '${RBAC_PROJECT_VIEW_USER}', assign Standard User global role
    ...               and the virt-project-view project role in '${HARVESTER_PROJECT_NAME}'.
    Given RBAC test user does not exist    ${RBAC_PROJECT_VIEW_USER}
    When RBAC test user is created    ${RBAC_PROJECT_VIEW_USER}
    Then Standard User role is assigned to    ${RBAC_PROJECT_VIEW_USER}
    And Project role is assigned to user    ${RBAC_PROJECT_VIEW_USER}
    ...    ${SUITE_CLUSTER_ID}    ${SUITE_PROJECT_ID}    ${RBAC_PROJECT_VIEW_ROLE}

Test TC3 Verify - Project View Can Read VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify
    [Documentation]    Confirm proj-viewer can GET VMs in the project namespace.
    Then User can read VMs in namespace    ${RBAC_PROJECT_VIEW_USER}    ${HARVESTER_PROJECT_NAMESPACE}

Test TC3 Verify - Project View Is Denied In Default Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-viewer cannot GET VMs in 'default' (outside project).
    Then User cannot read VMs in namespace    ${RBAC_PROJECT_VIEW_USER}    default

Test TC3 Verify - Project View Cannot Write VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-viewer cannot CREATE VMs even in the project namespace.
    Then User cannot write VMs in namespace    ${RBAC_PROJECT_VIEW_USER}    ${HARVESTER_PROJECT_NAMESPACE}

# ──────────────────────────────────────────────────────────────────────────────
# TC4: Project Role – Manage Virtualization Resources
# ──────────────────────────────────────────────────────────────────────────────
Test TC4 - Assign Project Manage Role
    [Tags]    p0    rbac    project-role
    [Documentation]    Create '${RBAC_PROJECT_MANAGE_USER}', assign Standard User global role
    ...               and the virt-project-manage project role in '${HARVESTER_PROJECT_NAME}'.
    Given RBAC test user does not exist    ${RBAC_PROJECT_MANAGE_USER}
    When RBAC test user is created    ${RBAC_PROJECT_MANAGE_USER}
    Then Standard User role is assigned to    ${RBAC_PROJECT_MANAGE_USER}
    And Project role is assigned to user    ${RBAC_PROJECT_MANAGE_USER}
    ...    ${SUITE_CLUSTER_ID}    ${SUITE_PROJECT_ID}    ${RBAC_PROJECT_MANAGE_ROLE}

Test TC4 Verify - Project Manage Can Read VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify
    [Documentation]    Confirm proj-manager can GET VMs in the project namespace.
    Then User can read VMs in namespace    ${RBAC_PROJECT_MANAGE_USER}    ${HARVESTER_PROJECT_NAMESPACE}

Test TC4 Verify - Project Manage Is Denied In Default Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-manager cannot GET VMs in 'default' (outside project).
    Then User cannot read VMs in namespace    ${RBAC_PROJECT_MANAGE_USER}    default

Test TC4 Verify - Project Manage Can Write VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify
    [Documentation]    Confirm proj-manager can CREATE VMs in the project namespace.
    Then User can write VMs in namespace    ${RBAC_PROJECT_MANAGE_USER}    ${HARVESTER_PROJECT_NAMESPACE}

Test Create Single Node RKE2 Cluster with Basic Workloads
    [Tags]    smoke    p0
    [Documentation]    Create a single-node RKE2 cluster and verify basic workloads
    ...               (CSI, Whoami, LB DHCP, LB Pool) are functional.
    Given Single node RKE2 cluster is created
    Then Harvester deployments should be ready    ${SINGLE_CLUSTER_ID}
    When Basic workloads are deployed on single node cluster
    Then Basic workloads should be active on single node cluster

Test RWX Volume On Single Node Cluster
    [Tags]    p1    rwx
    [Documentation]    Enable storage network on the single-node cluster (requires
    ...               stopping and restarting the VM), create an RWX StorageClass,
    ...               PVC, and StatefulSet with 2 replicas, then verify data written
    ...               by one pod is readable from the other. Validates Harvester CSI
    ...               driver RWX volume support end-to-end including the storage
    ...               network lifecycle.
    Skip    Reason: Requires two network interfaces, currently hangs during creation. Needs revisit.
    Given Single node cluster is available
    And Storage network is enabled for RWX
    And Single node cluster should be ready
    And Basic workloads should be active on single node cluster
    When RWX volume is created on single node cluster
    And RWX StatefulSet with 2 replicas is deployed on single node cluster
    Then RWX StatefulSet should be ready on single node cluster
    And RWX shared data should be accessible across pods on single node cluster
    # [Teardown]    Cleanup RWX test resources on single node cluster

Test Create Multi Node RKE2 Cluster
    [Tags]    p0    cloudprovider    csi
    [Documentation]    Create and verify a 3-node RKE2 cluster.
    When Multi node RKE2 cluster is created
    Then Harvester deployments should be ready    ${MULTI_CLUSTER_ID}

Test CSI Deployment
    [Tags]    p0    csi
    [Documentation]    Deploy a CSI workload with PVC on the multi-node cluster.
    Given Multi node cluster is available
    When CSI workload with PVC is deployed
    Then CSI deployment and PVC should be active

Test Load Balancer DHCP Mode
    [Tags]    p0    cloudprovider
    [Documentation]    Deploy a Whoami workload and create a LoadBalancer service in DHCP mode.
    Given Multi node cluster is available
    And Whoami workload is deployed    dhcp
    And Whoami deployment should be active    dhcp
    When Load balancer is created in DHCP mode    dhcp
    Then DHCP load balancer should be serving traffic

Test Load Balancer Pool Mode
    [Tags]    p0    cloudprovider
    [Documentation]    Deploy a Whoami workload and create a LoadBalancer service in IP Pool mode.
    Given Multi node cluster is available
    And Whoami workload is deployed    pool
    And Whoami deployment should be active    pool
    When Load balancer is created in pool mode    pool
    Then Pool load balancer should be serving traffic

Test Scale Up RKE2 Cluster
    [Tags]    p0
    [Documentation]    Scale up the multi-node cluster by adding a worker node.
    Given Multi node cluster is available
    When Worker pool with 1 node is added
    Then Multi node cluster should be ready

Test Verify Workloads After Scale Up
    [Tags]    p0
    [Documentation]    Verify existing workloads and Harvester deployments still running after scale up.
    Given Multi node cluster is available
    Then All existing workloads should be active

Test New Workloads After Scale Up
    [Tags]    p0
    [Documentation]    Create new CSI workload after scale up to verify cluster health.
    Given Multi node cluster is available
    When New CSI workload is deployed    scaleup
    Then New CSI workload should be active    scaleup
    And Harvester deployments should be ready    ${MULTI_CLUSTER_ID}
    [Teardown]    Cleanup temporary workloads    scaleup

Test Scale Down RKE2 Cluster
    [Tags]    p0
    [Documentation]    Scale down the multi-node cluster by removing the worker pool.
    Given Multi node cluster is available
    When Worker pool is removed
    Then Multi node cluster should be ready

Test Upgrade RKE2 Cluster
    [Tags]    p1
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
    [Tags]    p0
    [Documentation]    Delete all workloads from the multi-node cluster.
    Given Multi node cluster is available
    When All test workloads are removed from cluster
    Then Workloads should be cleaned up

Test Delete RKE2 Clusters
    [Tags]    p0
    [Documentation]    Delete both single-node and multi-node clusters.
    When Single node RKE2 cluster is deleted
    And Multi node RKE2 cluster is deleted
    Then Clusters should be deleted

Test Create Single Node Custom RKE2 Cluster with Basic Workloads
    [Tags]     custom    p2
    [Documentation]    Create a single-node custom RKE2 cluster with Harvester
    ...               cloud provider and verify basic workloads (CSI, Whoami, LB)
    ...               are functional.
    Given Single node custom RKE2 cluster is created
    Then Harvester deployments should be ready    ${CUSTOM_CLUSTER_ID}
    When Basic workloads are deployed on single node custom cluster
    Then Basic workloads should be active on single node custom cluster
    [Teardown]    Cleanup custom cluster test resources

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
    [Teardown]    Cleanup import cluster test resources
