*** Settings ***
Documentation    Rancher Integration RBAC Tests
...
...             Validates the harvester-rbac Helm chart installation, role assignment,
...             and resource-access verification for all four RBAC roles defined in:
...               - test-plan-ui.md (role assignment steps)
...               - test-plan-automated.md (API token + kubectl verification)
...
...             Four role types are covered:
...               TC1: Cluster role  – View Virtualization Resources   (virt-cluster-view)
...               TC2: Cluster role  – Manage Virtualization Resources (virt-cluster-manage)
...               TC3: Project role  – View Virtualization Resources   (virt-project-view)
...               TC4: Project role  – Manage Virtualization Resources (virt-project-manage)
...
...             Verification approach (per test-plan-automated.md):
...               1. Authenticate as the test user to obtain an API token.
...               2. Call Rancher's generateKubeconfig API to get a cluster kubeconfig.
...               3. Run kubectl auth can-i get/create virtualmachines.kubevirt.io to verify access.
...               4. For project-role users: also confirm denied on the 'default' namespace.
...
...             Prerequisites:
...               - RANCHER_ENDPOINT, RANCHER_USERNAME, RANCHER_PASSWORD are configured
...               - HARVESTER_ENDPOINT, HARVESTER_USERNAME, HARVESTER_PASSWORD are configured
...               - Harvester is NOT yet imported into Rancher (suite setup handles import/teardown)
...               - helm and kubectl CLIs are available on the test runner
Test Tags        rancher    rbac    regression

Resource         ../../../keywords/rancher.resource
Resource         ../../../keywords/variables.resource

Suite Setup      Suite Setup For RBAC Tests
Suite Teardown   Suite Teardown For RBAC Tests

*** Variables ***
# Suite-scoped resolved IDs – populated in Suite Setup.
${SUITE_CLUSTER_ID}    ${EMPTY}
${SUITE_PROJECT_ID}    ${EMPTY}

# harvester-rbac chart constants
${RBAC_CLUSTER_ID}              local
${RBAC_CHART_REPO_NAME}         rancher-charts
${RBAC_CHART_NAME}              harvester-rbac
${RBAC_CHART_VERSION}           110.0.0+up0.1.1
${RBAC_CHART_RELEASE_NAME}      harvester-rbac
${RBAC_CHART_NAMESPACE}         default

# Rancher project used for project-role tests
${HARVESTER_PROJECT_NAME}       Default
${HARVESTER_PROJECT_NAMESPACE}  rbactestns

# Test users (one per role)
${RBAC_CLUSTER_VIEW_USER}       virt-viewer
${RBAC_CLUSTER_MANAGE_USER}     virt-manager
${RBAC_PROJECT_VIEW_USER}       proj-viewer
${RBAC_PROJECT_MANAGE_USER}     proj-manager

# RoleTemplate names created by the harvester-rbac chart
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
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_CLUSTER_VIEW_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    get    virtualmachines.kubevirt.io    default
    Log    [TC1 cluster-view read] auth can-i get: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=virt-viewer should be able to get VMs in 'default' namespace. Output: ${output}

Test TC1 Verify - Cluster View Cannot Write VMs
    [Tags]    p0    rbac    cluster-role    verify    negative
    [Documentation]    Confirm virt-viewer cannot CREATE VMs in 'default' namespace.
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_CLUSTER_VIEW_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    create    virtualmachines.kubevirt.io    default
    Log    [TC1 cluster-view write] auth can-i create: ok=${ok}, output=${output}
    Should Not Be True    ${ok}
    ...    msg=virt-viewer should NOT be able to create VMs. Output: ${output}

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
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_CLUSTER_MANAGE_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    get    virtualmachines.kubevirt.io    default
    Log    [TC2 cluster-manage read] auth can-i get: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=virt-manager should be able to get VMs in 'default' namespace. Output: ${output}

Test TC2 Verify - Cluster Manage Can Write VMs
    [Tags]    p0    rbac    cluster-role    verify
    [Documentation]    Confirm virt-manager can CREATE VMs in 'default' namespace.
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_CLUSTER_MANAGE_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    create    virtualmachines.kubevirt.io    default
    Log    [TC2 cluster-manage write] auth can-i create: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=virt-manager should be able to create VMs. Output: ${output}

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
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_VIEW_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    get    virtualmachines.kubevirt.io    ${HARVESTER_PROJECT_NAMESPACE}
    Log    [TC3 project-view read] auth can-i get: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=proj-viewer should be able to get VMs in '${HARVESTER_PROJECT_NAMESPACE}'. Output: ${output}

Test TC3 Verify - Project View Is Denied In Default Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-viewer cannot GET VMs in 'default' (outside project).
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_VIEW_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access    ${kubeconfig}    get    virtualmachines.kubevirt.io    default
    Log    [TC3 project-view read denied] auth can-i get: ok=${ok}, output=${output}
    Should Not Be True    ${ok}
    ...    msg=proj-viewer should NOT be able to get VMs in 'default'. Output: ${output}

Test TC3 Verify - Project View Cannot Write VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-viewer cannot CREATE VMs even in the project namespace.
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_VIEW_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    create    virtualmachines.kubevirt.io    ${HARVESTER_PROJECT_NAMESPACE}
    Log    [TC3 project-view write] auth can-i create: ok=${ok}, output=${output}
    Should Not Be True    ${ok}
    ...    msg=proj-viewer should NOT be able to create VMs. Output: ${output}

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
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_MANAGE_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    get    virtualmachines.kubevirt.io    ${HARVESTER_PROJECT_NAMESPACE}
    Log    [TC4 project-manage read] auth can-i get: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=proj-manager should be able to get VMs in '${HARVESTER_PROJECT_NAMESPACE}'. Output: ${output}

Test TC4 Verify - Project Manage Is Denied In Default Namespace
    [Tags]    p0    rbac    project-role    verify    negative
    [Documentation]    Confirm proj-manager cannot GET VMs in 'default' (outside project).
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_MANAGE_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access    ${kubeconfig}    get    virtualmachines.kubevirt.io    default
    Log    [TC4 project-manage read denied] auth can-i get: ok=${ok}, output=${output}
    Should Not Be True    ${ok}
    ...    msg=proj-manager should NOT be able to get VMs in 'default'. Output: ${output}

Test TC4 Verify - Project Manage Can Write VMs In Project Namespace
    [Tags]    p0    rbac    project-role    verify
    [Documentation]    Confirm proj-manager can CREATE VMs in the project namespace.
    ${kubeconfig}=    Generate User Kubeconfig
    ...    ${RBAC_PROJECT_MANAGE_USER}    ${RBAC_USER_PASSWORD}    ${SUITE_CLUSTER_ID}
    ${ok}    ${output}=    Verify Resource Access
    ...    ${kubeconfig}    create    virtualmachines.kubevirt.io    ${HARVESTER_PROJECT_NAMESPACE}
    Log    [TC4 project-manage write] auth can-i create: ok=${ok}, output=${output}
    Should Be True    ${ok}
    ...    msg=proj-manager should be able to create VMs. Output: ${output}
