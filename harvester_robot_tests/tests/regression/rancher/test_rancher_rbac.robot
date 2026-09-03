*** Settings ***
Documentation    Rancher RBAC Integration Test Cases
...             Installs the harvester-rbac chart and verifies cluster-role and
...             project-role RBAC scenarios for Harvester virtualization resources.
Test Tags        rancher    rke2    regression
Resource         ../../../keywords/rancher.resource

Suite Setup      Get Or Create Rancher Test Environment
Suite Teardown   Teardown Rancher Test Suite    cleanup_rbac=${True}
Test Setup       Skip RBAC Tests If Chart Not Installed

*** Variables ***
${RBAC_CLUSTER_ID}              local
${RBAC_CHART_REPO_NAME}         rancher-charts
${RBAC_CHART_NAME}              harvester-rbac
${RBAC_CHART_INSTALLED}         ${False}
${RBAC_CHART_RELEASE_NAME}      harvester-rbac
${RBAC_CHART_NAMESPACE}         default
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
# TC0: Install and verify the harvester-rbac chart prerequisite
# ──────────────────────────────────────────────────────────────────────────────
Test Install Harvester RBAC Chart
    [Tags]    p0    rbac    chart-install
    [Documentation]    Install the harvester-rbac chart on the local cluster and
    ...               verify it becomes ready. The cluster-role/project-role RBAC
    ...               test cases below are skipped if this test does not pass.
    Install Harvester RBAC Chart On Local Cluster
    Setup RBAC Test Prerequisites
    Set Suite Variable    ${RBAC_CHART_INSTALLED}    ${True}

# ──────────────────────────────────────────────────────────────────────────────
# TC1: Cluster Role – View Virtualization Resources
# ──────────────────────────────────────────────────────────────────────────────
Test TC1 - Assign Cluster View Role
    [Tags]    p1    rbac    cluster-role
    [Documentation]    Create '${RBAC_CLUSTER_VIEW_USER}', assign Standard User global role
    ...               and the virt-cluster-view cluster role on the Harvester cluster.
    Given RBAC test user does not exist    ${RBAC_CLUSTER_VIEW_USER}
    When RBAC test user is created    ${RBAC_CLUSTER_VIEW_USER}
    Then Standard User role is assigned to    ${RBAC_CLUSTER_VIEW_USER}
    And Cluster role is assigned to user    ${RBAC_CLUSTER_VIEW_USER}
    ...    ${SUITE_CLUSTER_ID}    ${RBAC_CLUSTER_VIEW_ROLE}

Test TC1 Verify - Cluster View Can Read VMs
    [Tags]    p1    rbac    cluster-role    verify
    [Documentation]    Confirm virt-viewer can GET VMs in 'default' namespace.
    Then User can read VMs in namespace    ${RBAC_CLUSTER_VIEW_USER}    default

Test TC1 Verify - Cluster View Cannot Write VMs
    [Tags]    p1    rbac    cluster-role    verify    negative
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
