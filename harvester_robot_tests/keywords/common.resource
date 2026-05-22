*** Settings ***
Documentation    Common Keywords
Library          ../libs/keywords/common_keywords.py
Library          ../libs/keywords/image_keywords.py
Library          ../libs/keywords/network_keywords.py
Library          ../libs/keywords/volume_keywords.py
Resource         variables.resource


*** Keywords ***
Set up test environment
    [Documentation]    Initialize test environment
    Log    Setting up test environment
    common_keywords.init harvester api client    ${HARVESTER_ENDPOINT}    ${HARVESTER_USERNAME}    ${HARVESTER_PASSWORD}
    common_keywords.init k8s api client

Cleanup test resources
    [Documentation]    Clean up all resources created during tests
    Log    Cleaning up test resources
    Run Keyword And Ignore Error    common_keywords.Cleanup VMs
    Run Keyword And Ignore Error    common_keywords.Cleanup volumes
    Run Keyword And Ignore Error    common_keywords.Cleanup images
    Run Keyword And Ignore Error    common_keywords.Cleanup networks
    Run Keyword And Ignore Error    common_keywords.Cleanup backups

List Pods By Label
    [Arguments]    ${namespace}    ${label_selector}   ${status}=${None}
    [Documentation]    Get pods by label selector
    ${pods}=    common_keywords.list_pods_by_label    ${namespace}    ${label_selector}    ${status}
    RETURN    ${pods}

Count Pods By Label
    [Arguments]    ${namespace}    ${label_selector}   ${status}=${None}
    [Documentation]    Get pods by label selector
    ${pods}=    common_keywords.list_pods_by_label    ${namespace}    ${label_selector}    ${status}
    ${count}=   Get Length    ${pods}
    RETURN    ${count}

Suite Setup For Shared Resources
    [Documentation]    Suite setup for shared resources
    Log    Setting up shared resources for the test suite

    # Initialize test variables
    ${timestamp}=    Evaluate    __import__('datetime').datetime.now().strftime("%Y%m%d%H%M%S")
    Set Suite Variable    ${UNIQUE_NAME}    ${timestamp}
    Set Suite Variable    ${VLAN_NETWORK_NAME}    vlan-network-${VLAN_ID}
    # Harvester enforces a 12-character max on ClusterNetwork and VlanConfig names.
    ${ts_short}=    Evaluate    '${timestamp}'[-7:]
    Set Suite Variable    ${CLUSTER_NETWORK_NAME}    cnet-${ts_short}
    Set Suite Variable    ${VLAN_CONFIG_NAME}    vcfg-${ts_short}
    Set Suite Variable    ${IP_POOL_NAME}    ippool-vlan${VLAN_ID}
    Set Suite Variable    ${IMAGE_NAME}    opensuse-${timestamp}

    # Create shared resources
    network_keywords.create_cluster_network    ${CLUSTER_NETWORK_NAME}
    network_keywords.create_vlan_config    ${VLAN_CONFIG_NAME}    ${CLUSTER_NETWORK_NAME}    ${VLAN_NIC}
    network_keywords.wait_for_cluster_network_ready    ${CLUSTER_NETWORK_NAME}
    network_keywords.create_vlan_network    ${VLAN_NETWORK_NAME}    ${VLAN_ID}    ${CLUSTER_NETWORK_NAME}
    network_keywords.create_ip_pool
    ...    ${IP_POOL_NAME}
    ...    ${IP_POOL_SUBNET}
    ...    ${IP_POOL_START}
    ...    ${IP_POOL_END}
    ...    ${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
    image_keywords.create image from url    ${IMAGE_NAME}    ${OPENSUSE_IMAGE_URL}
    image_keywords.wait for image downloaded    ${IMAGE_NAME}

    Log    Test environment ready (image: ${IMAGE_NAME}, vlan: ${VLAN_NETWORK_NAME}, timestamp: ${timestamp})    console=yes

Suite Teardown For Shared Resources
    [Documentation]    Cleanup all resources after tests.
    Log    Running shared resources teardown

    # Delete shared resources
    Run Keyword And Ignore Error    network_keywords.delete_ip_pool    ${IP_POOL_NAME}
    Run Keyword And Ignore Error    network_keywords.delete_vlan_network    ${VLAN_NETWORK_NAME}
    Run Keyword And Ignore Error    network_keywords.delete_vlan_config    ${VLAN_CONFIG_NAME}
    Run Keyword And Ignore Error    network_keywords.wait_for_vlan_config_deleted    ${VLAN_CONFIG_NAME}
    Run Keyword And Ignore Error    network_keywords.delete_cluster_network    ${CLUSTER_NETWORK_NAME}
    Run Keyword And Ignore Error    volume_keywords.cleanup_volumes
    Run Keyword And Ignore Error    image_keywords.delete image    ${IMAGE_NAME}

    Cleanup test resources
    Log    Suite teardown completed for shared resources
