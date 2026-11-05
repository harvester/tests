*** Settings ***
Documentation    Rancher Windows Worker Integration Test Cases (RKE2)
...             Provision an RKE2 cluster on Harvester through Rancher's Harvester
...             node driver with a Linux control plane and a Windows Server worker
...             pool (machineOS windows). Covers node readiness and cloud provider
...             initialization, the Windows VM settings applied by the node driver
...             (harvester-os flag), Windows to Linux pod networking, scaling the
...             Windows pool and cluster deletion.
...             Requires WINDOWS_IMAGE_URL (see variables.resource) and a Harvester
...             node driver with Windows support; otherwise the suite is skipped.
Test Tags        rancher    rke2    windows    regression
Resource         ../../../keywords/rancher.resource

Suite Setup      Setup Windows Worker Suite
Suite Teardown   Teardown Windows Worker Suite

*** Keywords ***
Setup Windows Worker Suite
    Get Or Create Rancher Test Environment
    Setup Windows Worker Test Variables

Teardown Windows Worker Suite
    Cleanup Windows worker test resources
    Teardown Rancher Test Suite

*** Test Cases ***
Test Create RKE2 Cluster With Windows Worker Pool
    [Tags]    p1
    [Documentation]    Create a Linux RKE2 cluster and add a Windows worker pool.
    ...               The Windows node must become Ready and be initialized by
    ...               the Harvester cloud provider (providerID set, no
    ...               uninitialized taint), and its VM must carry the Windows
    ...               settings and Cloudbase-Init user data.
    Given Windows worker prerequisites are met
    And Windows image is created
    When RKE2 cluster with a Windows worker pool is created
    Then Windows nodes should be ready    1
    And Windows worker VMs should use Windows settings

Test Windows Workload Reaches Linux Service
    [Tags]    p1
    [Documentation]    A Windows pod reaches a Linux service through cluster DNS.
    Given Windows cluster is available
    When Linux whoami service is deployed on Windows cluster
    Then Windows pod should reach Linux whoami service
    [Teardown]    Cleanup Windows workload test resources

Test Scale Windows Worker Pool
    [Tags]    p1
    [Documentation]    Scale the Windows pool to 2 machines (unique, NetBIOS
    ...               length hostnames) and back to 1.
    Given Windows cluster is available
    When Windows worker pool is scaled to    2
    Then Windows nodes should be ready    2
    And Windows worker VMs should use Windows settings
    When Windows worker pool is scaled to    1
    Then Windows nodes should be ready    1

Test Delete RKE2 Cluster With Windows Workers
    [Tags]    p1
    [Documentation]    Delete the cluster; its Windows VMs are removed.
    Given Windows cluster is available
    When Windows cluster is deleted
    Then Windows worker VMs should be removed
