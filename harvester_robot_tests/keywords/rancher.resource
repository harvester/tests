*** Settings ***
Documentation    Rancher Integration Keywords - Reusable keywords for Rancher operations
Library          ../libs/keywords/rancher_keywords.py
Library          Collections
Library          String
Resource         variables.resource
Resource         common.resource

*** Keywords ***
# State Management
Rancher - Set State
    [Arguments]    ${key}    ${value}
    [Documentation]    Store state for later use between keywords
    Log    Setting state ${key} = ${value}
    set_state    ${key}    ${value}

Rancher - Get State
    [Arguments]    ${key}    ${default}=${NONE}
    [Documentation]    Retrieve stored state
    ${value}=    get_state    ${key}    ${default}
    RETURN    ${value}

Rancher - Clear State
    [Arguments]    ${key}=${NONE}
    [Documentation]    Clear state - either specific key or all
    clear_state    ${key}

Rancher - Generate Unique Name
    [Arguments]    ${prefix}=test
    [Documentation]    Generate unique name with timestamp
    ${name}=    generate_unique_name    ${prefix}
    Log    Generated unique name: ${name}
    RETURN    ${name}

# Harvester Management Cluster Operations
Rancher - Create Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Create Harvester management cluster entry in Rancher (Import Existing)
    ...               Args:
    ...                   cluster_name: Name of the cluster entry to create
    ...               Returns:
    ...                   dict: Cluster data
    Log    Creating Harvester management cluster: ${cluster_name}
    ${cluster}=    create_harvester_mgmt_cluster    ${cluster_name}
    RETURN    ${cluster}

Rancher - Get Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Get Harvester management cluster details
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...               Returns:
    ...                   dict: Cluster data or None if not found
    ${cluster}=    get_harvester_mgmt_cluster    ${cluster_name}
    RETURN    ${cluster}

Rancher - Delete Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Delete Harvester management cluster entry
    ...               Args:
    ...                   cluster_name: Name of the cluster to delete
    Log    Deleting Harvester management cluster: ${cluster_name}
    delete_harvester_mgmt_cluster    ${cluster_name}

Rancher - Wait For Cluster ID
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for cluster to get its internal ID (status.clusterName)
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Cluster data with ID
    Log    Waiting for cluster ${cluster_name} to get cluster ID
    ${cluster}=    wait_for_cluster_id    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

Rancher - Wait For Harvester Ready
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for Harvester cluster to be ready in Rancher
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds (default: WAIT_TIMEOUT)
    ...               Returns:
    ...                   dict: Cluster data when ready
    Log    Waiting for Harvester cluster ${cluster_name} to be ready
    ${cluster}=    wait_for_harvester_ready    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

# Import Harvester Operations
Rancher - Get Cluster Registration URL
    [Arguments]    ${cluster_id}    ${rancher_endpoint}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Get cluster registration URL for importing Harvester
    ...               Args:
    ...                   cluster_id: Internal cluster ID (e.g. c-m-xxxxx)
    ...                   rancher_endpoint: Rancher server endpoint
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   str: Registration manifest URL
    ${url}=    get_cluster_registration_url    ${cluster_id}    ${rancher_endpoint}    ${timeout}
    Log    Registration URL: ${url}
    RETURN    ${url}

Rancher - Set Cluster Registration URL
    [Arguments]    ${url}
    [Documentation]    Set cluster-registration-url setting in Harvester
    ...               Args:
    ...                   url: Registration URL to set
    Log    Setting cluster-registration-url
    set_cluster_registration_url    ${url}

Rancher - Get All RKE2 Versions
    [Arguments]    ${rancher_endpoint}    ${max_versions}=${NONE}
    [Documentation]    Get all available RKE2 versions from Rancher
    ...               Args:
    ...                   rancher_endpoint: Rancher server endpoint
    ...                   max_versions: Maximum number of versions to return (None = all)
    ...               Returns:
    ...                   list: List of RKE2 version strings sorted newest first
    Log    Getting all RKE2 versions from Rancher
    ${versions}=    get_all_rke2_versions    ${rancher_endpoint}    ${max_versions}
    RETURN    ${versions}

Rancher - Resolve RKE2 Versions
    [Arguments]    ${versions_input}    ${rancher_endpoint}    ${max_versions}=10
    [Documentation]    Resolve RKE2 versions based on input specification.
    ...               Handles special values:
    ...               - "all": Get all available versions (limited by max_versions)
    ...               - "latest": Get only the latest version
    ...               - "v1.28,v1.29": Get latest version matching each prefix
    ...               - "v1.28.15+rke2r1": Use specific version as-is
    ...               Args:
    ...                   versions_input: Version specification string
    ...                   rancher_endpoint: Rancher server endpoint
    ...                   max_versions: Max versions when using "all" (default: 10)
    ...               Returns:
    ...                   list: List of resolved version strings
    Log    Resolving RKE2 versions from input: ${versions_input}
    ${versions}=    resolve_rke2_versions    ${versions_input}    ${rancher_endpoint}    ${max_versions}
    RETURN    ${versions}

Rancher - Get RKE2 Version
    [Arguments]    ${target_version}    ${rancher_endpoint}
    [Documentation]    Get RKE2 version from Rancher that matches target version
    ...               Args:
    ...                   target_version: Target version prefix (e.g. 'v1.28')
    ...                   rancher_endpoint: Rancher server endpoint
    ...               Returns:
    ...                   str: Full RKE2 version (e.g. 'v1.28.15+rke2r1')
    Log    Getting RKE2 version for target: ${target_version}
    ${version}=    get_rke2_version    ${target_version}    ${rancher_endpoint}
    RETURN    ${version}

Rancher - Import Harvester To Rancher
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Full workflow to import Harvester to Rancher
    ...               Args:
    ...                   cluster_name: Name for the Harvester entry in Rancher
    ...                   timeout: Timeout for the import operation
    ...               Returns:
    ...                   dict: Harvester cluster data
    Log    Importing Harvester to Rancher as: ${cluster_name}
    ${cluster}=    import_harvester_to_rancher    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

# Cloud Credential Operations
Rancher - Create Cloud Credential
    [Arguments]    ${name}    ${kubeconfig}    ${cluster_id}
    [Documentation]    Create cloud credential for Harvester
    ...               Args:
    ...                   name: Name for the credential
    ...                   kubeconfig: Kubeconfig content
    ...                   cluster_id: Harvester cluster ID
    ...               Returns:
    ...                   dict: Credential data
    Log    Creating cloud credential: ${name}
    ${credential}=    create_cloud_credential    ${name}    ${kubeconfig}    ${cluster_id}
    RETURN    ${credential}

Rancher - Delete Cloud Credential
    [Arguments]    ${credential_id}
    [Documentation]    Delete cloud credential
    ...               Args:
    ...                   credential_id: ID of the credential to delete
    Log    Deleting cloud credential: ${credential_id}
    delete_cloud_credential    ${credential_id}

# RKE2 Cluster Operations
Rancher - Create RKE2 Cluster
    [Arguments]    ${name}    ${cloud_provider_config_id}    ${hostname_prefix}
    ...            ${harvester_config_name}    ${k8s_version}    ${cloud_credential_id}
    ...            ${quantity}=1    ${ingress}=${INGRESS_CONTROLLER}
    [Documentation]    Create RKE2 cluster on Harvester
    ...               Args:
    ...                   name: Cluster name
    ...                   cloud_provider_config_id: Cloud provider config secret ID
    ...                   hostname_prefix: Prefix for node hostnames
    ...                   harvester_config_name: Harvester config name
    ...                   k8s_version: Kubernetes version
    ...                   cloud_credential_id: Cloud credential ID
    ...                   quantity: Number of nodes (default: 1)
    ...                   ingress: Ingress controller (default: INGRESS_CONTROLLER)
    ...               Returns:
    ...                   dict: Cluster data
    Log    Creating RKE2 cluster: ${name}
    ${cluster}=    create_rke2_cluster    ${name}    ${cloud_provider_config_id}
    ...            ${hostname_prefix}    ${harvester_config_name}    ${k8s_version}
    ...            ${cloud_credential_id}    ${quantity}    ${ingress}
    RETURN    ${cluster}

Rancher - Get RKE2 Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Get RKE2 cluster details
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...               Returns:
    ...                   dict: Cluster data or None if not found
    ${cluster}=    get_rke2_cluster    ${cluster_name}
    RETURN    ${cluster}

Rancher - Delete RKE2 Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Delete RKE2 cluster
    ...               Args:
    ...                   cluster_name: Name of the cluster to delete
    Log    Deleting RKE2 cluster: ${cluster_name}
    delete_rke2_cluster    ${cluster_name}

Rancher - Wait For RKE2 Cluster Ready
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for RKE2 cluster to be ready
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Cluster data when ready
    Log    Waiting for RKE2 cluster ${cluster_name} to be ready
    ${cluster}=    wait_for_rke2_cluster_ready    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

Rancher - Wait For RKE2 Cluster Deleted
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for RKE2 cluster to be deleted
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   bool: True when deleted
    Log    Waiting for RKE2 cluster ${cluster_name} to be deleted
    ${result}=    wait_for_rke2_cluster_deleted    ${cluster_name}    ${timeout}
    RETURN    ${result}

Rancher - Scale RKE2 Cluster
    [Arguments]    ${cluster_name}    ${worker_count}    ${harvester_config_name}
    [Documentation]    Scale RKE2 cluster by adding/removing a worker-only machine pool.
    ...               Args:
    ...                   cluster_name: Name of the RKE2 cluster
    ...                   worker_count: Number of worker nodes (0 to remove worker pool)
    ...                   harvester_config_name: HarvesterConfig name for worker pool nodes
    Log    Scaling RKE2 cluster ${cluster_name}: worker_count=${worker_count}
    scale_rke2_cluster    ${cluster_name}    ${worker_count}    ${harvester_config_name}

Rancher - Upgrade RKE2 Cluster
    [Arguments]    ${cluster_name}    ${new_k8s_version}
    [Documentation]    Upgrade RKE2 cluster to a new Kubernetes version.
    ...               Args:
    ...                   cluster_name: Name of the RKE2 cluster
    ...                   new_k8s_version: Target Kubernetes version string
    Log    Upgrading RKE2 cluster ${cluster_name} to ${new_k8s_version}
    upgrade_rke2_cluster    ${cluster_name}    ${new_k8s_version}

Rancher - Get Next RKE2 Version
    [Arguments]    ${current_version}    ${rancher_endpoint}
    [Documentation]    Get the next (n+1) RKE2 version available on Rancher
    ...               for the same minor stream.
    ...               Args:
    ...                   current_version: Current RKE2 version (e.g. v1.31.4+rke2r1)
    ...                   rancher_endpoint: Rancher server endpoint
    ...               Returns:
    ...                   str: Next version string, or empty string if none available
    ${version}=    get_next_rke2_version    ${current_version}    ${rancher_endpoint}
    RETURN    ${version}

Rancher - Verify LB Response
    [Arguments]    ${url}    ${expected_text}=${NONE}
    [Documentation]    Verify LoadBalancer is responding with expected content
    ...               Args:
    ...                   url: URL to query
    ...                   expected_text: Text expected in response (optional)
    ...               Returns:
    ...                   bool: True if response matches
    Log    Verifying LB response from: ${url}
    ${result}=    verify_lb_response    ${url}    ${expected_text}
    RETURN    ${result}

Rancher - Verify LB Via Cluster
    [Arguments]    ${cluster_id}    ${service_name}    ${expected_text}=${NONE}
    ...            ${port}=8080    ${namespace}=default
    [Documentation]    Verify LoadBalancer via Rancher k8s service proxy.
    ...               Works regardless of whether the LB VIP is routable from
    ...               the test runner.
    ...               Args:
    ...                   cluster_id: Downstream cluster ID (e.g. c-m-xxxxx)
    ...                   service_name: Name of the LoadBalancer service
    ...                   expected_text: Text expected in response (optional)
    ...                   port: Service port (default 8080)
    ...                   namespace: Service namespace (default: default)
    Log    Verifying LB ${service_name} via cluster proxy
    ${result}=    verify_lb_via_cluster    ${cluster_id}    ${service_name}
    ...    ${port}    ${namespace}    ${expected_text}
    RETURN    ${result}

# Harvester Config Operations
Rancher - Create Harvester Config
    [Arguments]    ${name}    ${cpus}=${EMPTY}    ${mems}=${EMPTY}    ${disks}=${EMPTY}    ${image_id}=${EMPTY}
    ...            ${network_id}=${EMPTY}    ${ssh_user}=ubuntu    ${user_data}=${EMPTY}
    [Documentation]    Create Harvester config for RKE2 node template
    ...               Args:
    ...                   name: Config name
    ...                   cpus: Number of CPUs (default: uses DEFAULT_RKE2_NODE_CPUS from constant.py)
    ...                   mems: Memory in GB (default: uses DEFAULT_RKE2_NODE_MEMORY from constant.py)
    ...                   disks: Disk size in GB (default: uses DEFAULT_RKE2_NODE_DISK from constant.py)
    ...                   image_id: Image ID to use
    ...                   network_id: Network name
    ...                   ssh_user: SSH user (default: ubuntu)
    ...                   user_data: Cloud-init user data
    ...               Returns:
    ...                   dict: Config data
    Log    Creating Harvester config: ${name}
    ${config}=    create_harvester_config    ${name}    ${cpus}    ${mems}    ${disks}
    ...           ${image_id}    ${network_id}    ${ssh_user}    ${user_data}
    RETURN    ${config}

# Kubeconfig Operations
Rancher - Generate Kubeconfig
    [Arguments]    ${cluster_id}    ${cluster_name}
    [Documentation]    Generate full-access kubeconfig for a cluster (for cloud credentials)
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   cluster_name: Cluster name
    ...               Returns:
    ...                   str: Kubeconfig content
    Log    Generating kubeconfig for cluster: ${cluster_name}
    ${kubeconfig}=    generate_kubeconfig    ${cluster_id}    ${cluster_name}
    RETURN    ${kubeconfig}

Rancher - Generate Cloud Provider Kubeconfig
    [Arguments]    ${cluster_id}    ${cluster_name}
    [Documentation]    Generate cloud provider kubeconfig with external URL
    ...               (for cloud provider secret inside guest VM)
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   cluster_name: Cluster name
    ...               Returns:
    ...                   str: Kubeconfig content with external Rancher URL
    Log    Generating cloud provider kubeconfig for cluster: ${cluster_name}
    ${kubeconfig}=    generate_cloud_provider_kubeconfig    ${cluster_id}    ${cluster_name}
    RETURN    ${kubeconfig}

# Secret Operations
Rancher - Create Cloud Provider Secret
    [Arguments]    ${name}    ${kubeconfig}    ${cluster_name}
    [Documentation]    Create secret for cloud provider config
    ...               Args:
    ...                   name: Secret name
    ...                   kubeconfig: Kubeconfig content
    ...                   cluster_name: Cluster name for annotations
    ...               Returns:
    ...                   dict: Secret data
    Log    Creating cloud provider secret: ${name}
    ${secret}=    create_cloud_provider_secret    ${name}    ${kubeconfig}    ${cluster_name}
    RETURN    ${secret}

# Deployment Operations
Rancher - Create Deployment
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${image}    ${pvc}=${NONE}
    [Documentation]    Create deployment in guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    ...                   image: Container image
    ...                   pvc: PVC name to mount (optional)
    ...               Returns:
    ...                   dict: Deployment data
    Log    Creating deployment ${name} in cluster ${cluster_id}
    ${deployment}=    create_deployment    ${cluster_id}    ${namespace}    ${name}    ${image}    ${pvc}
    RETURN    ${deployment}

Rancher - Delete Deployment
    [Arguments]    ${cluster_id}    ${namespace}    ${name}
    [Documentation]    Delete deployment from guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    Log    Deleting deployment ${name} from cluster ${cluster_id}
    delete_deployment    ${cluster_id}    ${namespace}    ${name}

Rancher - Wait For Deployment Ready
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for deployment to be ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Deployment data when ready
    Log    Waiting for deployment ${name} to be ready
    ${deployment}=    wait_for_deployment_ready    ${cluster_id}    ${namespace}    ${name}    ${timeout}
    RETURN    ${deployment}

Rancher - Wait For Deployment Deleted
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for deployment to be deleted
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   bool: True when deleted
    Log    Waiting for deployment ${name} to be deleted
    ${result}=    wait_for_deployment_deleted    ${cluster_id}    ${namespace}    ${name}    ${timeout}
    RETURN    ${result}

# PVC Operations
Rancher - Create PVC
    [Arguments]    ${cluster_id}    ${name}    ${size}=1Gi    ${storage_class}=${NONE}
    [Documentation]    Create PVC in guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    ...                   size: Storage size (default: 1Gi)
    ...                   storage_class: Storage class name (optional)
    ...               Returns:
    ...                   dict: PVC data
    Log    Creating PVC ${name} in cluster ${cluster_id}
    ${pvc}=    create_pvc    ${cluster_id}    ${name}    ${size}    ${storage_class}
    RETURN    ${pvc}

Rancher - Delete PVC
    [Arguments]    ${cluster_id}    ${name}
    [Documentation]    Delete PVC from guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    Log    Deleting PVC ${name} from cluster ${cluster_id}
    delete_pvc    ${cluster_id}    ${name}

Rancher - Wait For PVC Bound
    [Arguments]    ${cluster_id}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for PVC to be bound
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: PVC data when bound
    Log    Waiting for PVC ${name} to be bound
    ${pvc}=    wait_for_pvc_bound    ${cluster_id}    ${name}    ${timeout}
    RETURN    ${pvc}

# Load Balancer Service Operations
Rancher - Create LB Service
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${target_deployment}
    ...            ${port}=8080    ${target_port}=80    ${ipam}=dhcp
    [Documentation]    Create LoadBalancer service
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Service name
    ...                   target_deployment: Deployment to target
    ...                   port: Service port (default: 8080)
    ...                   target_port: Target port (default: 80)
    ...                   ipam: IPAM mode - 'dhcp' or 'pool' (default: dhcp)
    ...               Returns:
    ...                   dict: Service data
    Log    Creating LoadBalancer service ${name} in cluster ${cluster_id}
    ${service}=    create_lb_service    ${cluster_id}    ${namespace}    ${name}
    ...            ${target_deployment}    ${port}    ${target_port}    ${ipam}
    RETURN    ${service}

Rancher - Delete LB Service
    [Arguments]    ${cluster_id}    ${name}
    [Documentation]    Delete LoadBalancer service
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: Service name
    Log    Deleting LoadBalancer service ${name} from cluster ${cluster_id}
    delete_lb_service    ${cluster_id}    ${name}

Rancher - Wait For LB Service Ready
    [Arguments]    ${cluster_id}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for LoadBalancer service to be ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: Service name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Service data when ready
    Log    Waiting for LoadBalancer service ${name} to be ready
    ${service}=    wait_for_lb_service_ready    ${cluster_id}    ${name}    ${timeout}
    RETURN    ${service}

Rancher - Query LB Service
    [Arguments]    ${url}
    [Documentation]    Query LoadBalancer service endpoint
    ...               Args:
    ...                   url: URL to query
    ...               Returns:
    ...                   tuple: (status_code, response_text)
    Log    Querying LoadBalancer service at: ${url}
    ${code}    ${text}=    query_lb_service    ${url}
    RETURN    ${code}    ${text}

Rancher - Verify LB Nginx Response
    [Arguments]    ${url}
    [Documentation]    Verify LoadBalancer returns nginx welcome page
    ...               Args:
    ...                   url: URL to query
    ...               Returns:
    ...                   bool: True if nginx welcome page found
    Log    Verifying nginx response from: ${url}
    ${result}=    verify_lb_nginx_response    ${url}
    RETURN    ${result}

# Harvester Deployments Check
Rancher - Wait For Harvester Deployments Ready
    [Arguments]    ${cluster_id}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for harvester-cloud-provider and harvester-csi-driver to be ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   timeout: Timeout in seconds
    Log    Waiting for Harvester deployments in cluster ${cluster_id}
    wait_for_harvester_deployments_ready    ${cluster_id}    ${timeout}

# VLAN Network Operations
Rancher - Create VLAN Network
    [Arguments]    ${name}    ${vlan_id}    ${cluster_network}
    [Documentation]    Create VLAN network
    ...               Args:
    ...                   name: Network name
    ...                   vlan_id: VLAN ID
    ...                   cluster_network: Cluster network name
    ...               Returns:
    ...                   dict: Network data
    Log    Creating VLAN network: ${name}
    ${network}=    create_vlan_network    ${name}    ${vlan_id}    ${cluster_network}
    RETURN    ${network}

Rancher - Delete VLAN Network
    [Arguments]    ${name}
    [Documentation]    Delete VLAN network
    ...               Args:
    ...                   name: Network name
    Log    Deleting VLAN network: ${name}
    delete_vlan_network    ${name}

# IP Pool Operations
Rancher - Get IP Pool
    [Arguments]    ${name}
    [Documentation]    Get IP pool by name, returns None if not found
    ...               Args:
    ...                   name: IP pool name
    ...               Returns:
    ...                   dict: IP pool data or None
    ${pool}=    get_ip_pool    ${name}
    RETURN    ${pool}

Rancher - Create IP Pool
    [Arguments]    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}
    [Documentation]    Create IP pool
    ...               Args:
    ...                   name: IP pool name
    ...                   subnet: Subnet CIDR
    ...                   start_ip: Start IP address
    ...                   end_ip: End IP address
    ...                   network_id: Network ID
    ...               Returns:
    ...                   dict: IP pool data
    Log    Creating IP pool: ${name}
    ${pool}=    create_ip_pool    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}
    RETURN    ${pool}

Rancher - Delete IP Pool
    [Arguments]    ${name}
    [Documentation]    Delete IP pool
    ...               Args:
    ...                   name: IP pool name
    Log    Deleting IP pool: ${name}
    delete_ip_pool    ${name}

# Image Operations
Rancher - Create Image
    [Arguments]    ${name}    ${url}
    [Documentation]    Create image by URL
    ...               Args:
    ...                   name: Image name
    ...                   url: URL to download image from
    ...               Returns:
    ...                   dict: Image data
    Log    Creating image: ${name}
    ${image}=    create_image    ${name}    ${url}
    RETURN    ${image}

Rancher - Wait For Image Ready
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for image to be ready
    ...               Args:
    ...                   name: Image name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Image data when ready
    Log    Waiting for image ${name} to be ready
    ${image}=    wait_for_image_ready    ${name}    ${timeout}
    RETURN    ${image}

Rancher - Delete Image
    [Arguments]    ${name}
    [Documentation]    Delete image
    ...               Args:
    ...                   name: Image name
    Log    Deleting image: ${name}
    delete_image    ${name}

# ============================================================
# BDD Keywords - Given (Preconditions)
# ============================================================
Multi node cluster is available
    [Documentation]    Verify multi-node cluster exists before proceeding.
    Skip If    '${MULTI_CLUSTER_ID}' == ''    Multi-node cluster not available

Next RKE2 version is available
    [Documentation]    Check if a newer RKE2 patch version exists on Rancher.
    ${next_version}=    Rancher - Get Next RKE2 Version    ${RKE2_VERSION}    ${RANCHER_ENDPOINT}
    Skip If    '${next_version}' == ''    No newer RKE2 version available for upgrade
    Set Suite Variable    ${NEXT_RKE2_VERSION}    ${next_version}
    Log    Next RKE2 version: ${next_version}    console=yes

# ============================================================
# BDD Keywords - When (Actions)
# ============================================================
Single node RKE2 cluster is created
    [Documentation]    Create a single-node RKE2 cluster and store its ID.
    Log    Creating single-node cluster: ${SINGLE_CLUSTER_NAME}    console=yes
    ${cluster_id}=    Create RKE2 Cluster With Full Setup
    ...    ${SINGLE_CLUSTER_NAME}    ${SINGLE_CONFIG_NAME}    ${RKE2_VERSION}    1
    Set Suite Variable    ${SINGLE_CLUSTER_ID}    ${cluster_id}
    Log    Single-node cluster created: ${SINGLE_CLUSTER_NAME} (${cluster_id})    console=yes

Basic workloads are deployed on single node cluster
    [Documentation]    Deploy CSI, Whoami, and LB services on the single-node cluster.
    # CSI workload
    ${pvc_name}=    Set Variable    pvc-${SINGLE_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${SINGLE_CLUSTER_NAME}
    Rancher - Create PVC    ${SINGLE_CLUSTER_ID}    ${pvc_name}    1Gi
    Rancher - Create Deployment    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    nginx:latest    ${pvc_name}
    # Whoami workload
    ${whoami_deploy}=    Set Variable    whoami-${SINGLE_CLUSTER_NAME}
    Rancher - Create Deployment    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    traefik/whoami:v1.11.0
    # LB DHCP
    ${lb_dhcp}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-dhcp
    Rancher - Create LB Service    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_dhcp}    ${whoami_deploy}    ipam=dhcp
    Rancher - Wait For LB Service Ready    ${SINGLE_CLUSTER_ID}    ${lb_dhcp}
    # LB Pool
    ${lb_pool}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-pool
    Rancher - Create LB Service    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_pool}    ${whoami_deploy}    ipam=pool
    Rancher - Wait For LB Service Ready    ${SINGLE_CLUSTER_ID}    ${lb_pool}

Multi node RKE2 cluster is created
    [Documentation]    Create a 3-node RKE2 cluster and store its ID.
    Log    Creating multi-node cluster: ${MULTI_CLUSTER_NAME}    console=yes
    ${cluster_id}=    Create RKE2 Cluster With Full Setup
    ...    ${MULTI_CLUSTER_NAME}    ${MULTI_CONFIG_NAME}    ${RKE2_VERSION}    3
    Set Suite Variable    ${MULTI_CLUSTER_ID}    ${cluster_id}
    Log    Multi-node cluster created: ${MULTI_CLUSTER_NAME} (${cluster_id})    console=yes

CSI workload with PVC is deployed
    [Documentation]    Create a PVC and nginx deployment using Harvester CSI.
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    Rancher - Create PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}    1Gi
    Rancher - Create Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}    nginx:latest    ${pvc_name}

Whoami workload is deployed
    [Documentation]    Deploy a Whoami workload for load balancer testing.
    ${deploy_name}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    Rancher - Create Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}    traefik/whoami:v1.11.0

Load balancer is created in DHCP mode
    [Documentation]    Create a LoadBalancer service using DHCP for IP assignment.
    ${whoami_deploy}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    ${lb_name}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-dhcp
    Rancher - Create LB Service    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_name}    ${whoami_deploy}    ipam=dhcp
    Rancher - Wait For LB Service Ready    ${MULTI_CLUSTER_ID}    ${lb_name}
    Set Suite Variable    ${LB_DHCP_NAME}    ${lb_name}

Load balancer is created in pool mode
    [Documentation]    Create a LoadBalancer service using an IP pool for IP assignment.
    ${whoami_deploy}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    ${lb_name}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-pool
    Rancher - Create LB Service    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_name}    ${whoami_deploy}    ipam=pool
    Rancher - Wait For LB Service Ready    ${MULTI_CLUSTER_ID}    ${lb_name}
    Set Suite Variable    ${LB_POOL_NAME}    ${lb_name}

Worker pool with 1 node is added
    [Documentation]    Scale up the multi-node cluster by adding a worker pool.
    Rancher - Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    1    ${MULTI_CONFIG_NAME}

Worker pool is removed
    [Documentation]    Scale down the multi-node cluster by removing the worker pool.
    Rancher - Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    0    ${MULTI_CONFIG_NAME}

Multi node cluster is upgraded to next version
    [Documentation]    Trigger RKE2 upgrade to the next available patch version.
    Log    Upgrading from ${RKE2_VERSION} to ${NEXT_RKE2_VERSION}    console=yes
    Rancher - Upgrade RKE2 Cluster    ${MULTI_CLUSTER_NAME}    ${NEXT_RKE2_VERSION}

New CSI workload is deployed
    [Arguments]    ${suffix}
    [Documentation]    Create a new PVC and nginx deployment for post-operation verification.
    ${pvc_name}=    Set Variable    pvc-${suffix}-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${suffix}-${MULTI_CLUSTER_NAME}
    Rancher - Create PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}    1Gi
    Rancher - Create Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}    nginx:latest    ${pvc_name}

All test workloads are removed from cluster
    [Documentation]    Delete all test deployments, PVCs, and LB services.
    ${csi_deploy}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    ${whoami_deploy}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-dhcp
    ${lb_pool}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-pool
    Rancher - Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Rancher - Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Rancher - Delete PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Rancher - Delete LB Service    ${MULTI_CLUSTER_ID}    ${lb_dhcp}
    Rancher - Delete LB Service    ${MULTI_CLUSTER_ID}    ${lb_pool}
    Rancher - Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Rancher - Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}

Single node RKE2 cluster is deleted
    [Documentation]    Delete the single-node RKE2 cluster and wait for removal.
    Log    Deleting: ${SINGLE_CLUSTER_NAME}    console=yes
    Rancher - Delete RKE2 Cluster    ${SINGLE_CLUSTER_NAME}
    Rancher - Wait For RKE2 Cluster Deleted    ${SINGLE_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

Multi node RKE2 cluster is deleted
    [Documentation]    Delete the multi-node RKE2 cluster and wait for removal.
    Log    Deleting: ${MULTI_CLUSTER_NAME}    console=yes
    Rancher - Delete RKE2 Cluster    ${MULTI_CLUSTER_NAME}
    Rancher - Wait For RKE2 Cluster Deleted    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

# ============================================================
# BDD Keywords - Then (Verifications)
# ============================================================
Harvester deployments should be ready
    [Arguments]    ${cluster_id}
    [Documentation]    Verify harvester-cloud-provider and CSI driver are active.
    Rancher - Wait For Harvester Deployments Ready    ${cluster_id}

Basic workloads should be active on single node cluster
    [Documentation]    Verify CSI, Whoami, and both LB services are functional on the single-node cluster.
    ${pvc_name}=    Set Variable    pvc-${SINGLE_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${SINGLE_CLUSTER_NAME}
    ${whoami_deploy}=    Set Variable    whoami-${SINGLE_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-dhcp
    ${lb_pool}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-pool
    Rancher - Wait For PVC Bound    ${SINGLE_CLUSTER_ID}    ${pvc_name}
    Rancher - Wait For Deployment Ready    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Rancher - Wait For Deployment Ready    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Rancher - Verify LB Via Cluster    ${SINGLE_CLUSTER_ID}    ${lb_dhcp}    Hostname:
    Rancher - Verify LB Via Cluster    ${SINGLE_CLUSTER_ID}    ${lb_pool}    Hostname:
    Log    All basic workloads verified on single-node cluster    console=yes

CSI deployment and PVC should be active
    [Documentation]    Verify the CSI PVC is bound and deployment is running.
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    Rancher - Wait For PVC Bound    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Rancher - Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Log    CSI deployment ready: ${deploy_name}    console=yes

Whoami deployment should be active
    [Documentation]    Verify the Whoami deployment is running.
    ${deploy_name}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    Rancher - Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Log    Whoami deployment ready: ${deploy_name}    console=yes

DHCP load balancer should be serving traffic
    [Documentation]    Verify the DHCP load balancer responds via Rancher proxy.
    Rancher - Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_DHCP_NAME}    Hostname:

Pool load balancer should be serving traffic
    [Documentation]    Verify the pool load balancer responds via Rancher proxy.
    Rancher - Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_POOL_NAME}    Hostname:

Multi node cluster should be ready
    [Documentation]    Wait for the multi-node cluster to become active and ready.
    Rancher - Wait For RKE2 Cluster Ready    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

All existing workloads should be active
    [Documentation]    Verify all system and application workloads are running.
    Rancher - Wait For Harvester Deployments Ready    ${MULTI_CLUSTER_ID}
    ${csi_deploy}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    ${whoami_deploy}=    Set Variable    whoami-${MULTI_CLUSTER_NAME}
    Rancher - Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Rancher - Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Rancher - Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_DHCP_NAME}    Hostname:
    Rancher - Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_POOL_NAME}    Hostname:
    Log    All existing workloads verified active    console=yes

New CSI workload should be active
    [Arguments]    ${suffix}
    [Documentation]    Verify the new CSI PVC and deployment are active.
    ${pvc_name}=    Set Variable    pvc-${suffix}-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${suffix}-${MULTI_CLUSTER_NAME}
    Rancher - Wait For PVC Bound    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Rancher - Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Log    New CSI deployment ready: ${deploy_name}    console=yes

Workloads should be cleaned up
    [Documentation]    Confirm workload cleanup is complete.
    Log    Workloads cleaned up    console=yes

Clusters should be deleted
    [Documentation]    Confirm cluster deletion is complete.
    Log    Clusters deleted    console=yes

# ============================================================
# Cleanup Keywords
# ============================================================
Cleanup temporary workloads
    [Arguments]    ${suffix}
    [Documentation]    Remove temporary CSI workload created during test.
    ${deploy_name}=    Set Variable    csi-${suffix}-${MULTI_CLUSTER_NAME}
    ${pvc_name}=    Set Variable    pvc-${suffix}-${MULTI_CLUSTER_NAME}
    Run Keyword And Ignore Error    Rancher - Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Run Keyword And Ignore Error    Rancher - Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Run Keyword And Ignore Error    Rancher - Delete PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}

Cleanup upgrade test resources
    [Documentation]    Clean up resources created during the upgrade test.
    Run Keyword And Ignore Error    Cleanup temporary workloads    upgrade
    Run Keyword And Ignore Error    Rancher - Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    0    ${MULTI_CONFIG_NAME}
    Run Keyword And Ignore Error    Rancher - Wait For RKE2 Cluster Ready    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

# ============================================================
# Shared cluster creation keyword
# ============================================================
Create RKE2 Cluster With Full Setup
    [Arguments]    ${cluster_name}    ${config_name}    ${rke2_version}    ${machine_count}
    ...            ${ingress}=${INGRESS_CONTROLLER}
    [Documentation]    Create RKE2 cluster with per-cluster resources
    ...               (cloud provider secret, harvester config).
    ...               Uses shared cloud credential from suite setup.
    ...               Returns cluster ID.

    # Cloud provider secret (per-cluster to avoid ownership collisions)
    ${secret}=    Rancher - Create Cloud Provider Secret    ${cluster_name}    ${CP_KUBECONFIG}    ${cluster_name}
    ${cloud_provider_config_id}=    Set Variable    ${secret}[metadata][namespace]:${secret}[metadata][name]

    # Harvester config (per-cluster for scale ops)
    Rancher - Create Harvester Config
    ...    ${config_name}
    ...    image_id=${DEFAULT_NAMESPACE}/${IMAGE_NAME}
    ...    network_id=${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
    ...    ssh_user=ubuntu

    # Create RKE2 cluster
    Rancher - Create RKE2 Cluster
    ...    ${cluster_name}
    ...    ${cloud_provider_config_id}
    ...    ${cluster_name}-
    ...    ${config_name}
    ...    ${rke2_version}
    ...    ${CLOUD_CREDENTIAL_ID}
    ...    ${machine_count}
    ...    ${ingress}

    # Wait for ready
    ${cluster}=    Rancher - Wait For RKE2 Cluster Ready    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Log    Cluster ready: ${cluster_name} (ID: ${cluster_id})    console=yes

    RETURN    ${cluster_id}

# ============================================================
# Setup and Teardown
# ============================================================
Suite Setup For Rancher Integration Tests
    [Documentation]    Initialize test environment for Rancher integration tests.
    Log    Setting up test environment for Rancher integration tests
    Set up test environment

    # Initialize test variables
    ${timestamp}=    Evaluate    __import__('datetime').datetime.now().strftime("%Y%m%d%H%M%S")
    Set Suite Variable    ${UNIQUE_NAME}    ${timestamp}
    Set Suite Variable    ${HARVESTER_CLUSTER_NAME}    hvst-${timestamp}
    Set Suite Variable    ${RKE2_CLUSTER_NAME}    rke2-${timestamp}
    Set Suite Variable    ${VLAN_NETWORK_NAME}    vlan-network-${VLAN_ID}
    Set Suite Variable    ${IP_POOL_NAME}    ippool-vlan${VLAN_ID}
    Set Suite Variable    ${IMAGE_NAME}    ubuntu-${timestamp}

    # Derive cluster and config names from RKE2_VERSION
    ${version_suffix}=    Replace String    ${RKE2_VERSION}    +    -
    ${version_suffix}=    Replace String    ${version_suffix}    .    -
    Set Suite Variable    ${SINGLE_CLUSTER_NAME}    ${RKE2_CLUSTER_NAME}-${version_suffix}-single
    Set Suite Variable    ${MULTI_CLUSTER_NAME}     ${RKE2_CLUSTER_NAME}-${version_suffix}-multi
    Set Suite Variable    ${SINGLE_CONFIG_NAME}     ${RKE2_CLUSTER_NAME}-${version_suffix}-single-config
    Set Suite Variable    ${MULTI_CONFIG_NAME}      ${RKE2_CLUSTER_NAME}-${version_suffix}-multi-config

    # Cluster tracking
    Set Suite Variable    ${HARVESTER_CLUSTER_ID}    ${EMPTY}
    Set Suite Variable    ${CLOUD_CREDENTIAL_ID}    ${EMPTY}
    Set Suite Variable    ${SINGLE_CLUSTER_ID}      ${EMPTY}
    Set Suite Variable    ${MULTI_CLUSTER_ID}       ${EMPTY}
    Set Suite Variable    ${LB_DHCP_NAME}           ${EMPTY}
    Set Suite Variable    ${LB_POOL_NAME}           ${EMPTY}
    Set Suite Variable    ${NEXT_RKE2_VERSION}      ${EMPTY}

    # Resolve RKE2 version (prefix like v1.34 -> full version like v1.34.5+rke2r1)
    ${is_full_version}=    Evaluate    '+' in '${RKE2_VERSION}'
    IF    not ${is_full_version}
        ${versions}=    Rancher - Resolve RKE2 Versions
        ...    ${RKE2_VERSION}
        ...    ${RANCHER_ENDPOINT}
        ...    1
        ${resolved}=    Get From List    ${versions}    0
        Set Suite Variable    ${RKE2_VERSION}    ${resolved}
        Log    Resolved RKE2 version: ${resolved}    console=yes
    END

    Log    Testing RKE2 version: ${RKE2_VERSION}    console=yes

    # Import Harvester to Rancher and verify readiness
    Import Harvester To Rancher In Setup
    ${cluster}=    Rancher - Get Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}
    Should Not Be Empty    ${cluster}    Harvester cluster not found in Rancher
    Log    Harvester integration verified    console=yes

    # Generate shared kubeconfigs and cloud credential (used by all clusters)
    ${cp_kubeconfig}=    Rancher - Generate Cloud Provider Kubeconfig
    ...    ${HARVESTER_CLUSTER_ID}    ${HARVESTER_CLUSTER_NAME}
    Set Suite Variable    ${CP_KUBECONFIG}    ${cp_kubeconfig}

    ${kubeconfig}=    Rancher - Generate Kubeconfig    ${HARVESTER_CLUSTER_ID}    ${HARVESTER_CLUSTER_NAME}
    ${credential}=    Rancher - Create Cloud Credential
    ...    ${RKE2_CLUSTER_NAME}
    ...    ${kubeconfig}
    ...    ${HARVESTER_CLUSTER_ID}
    Set Suite Variable    ${CLOUD_CREDENTIAL_ID}    ${credential}[id]

    # Create shared resources
    Rancher - Create VLAN Network    ${VLAN_NETWORK_NAME}    ${VLAN_ID}    ${VLAN_NIC}
    Rancher - Create IP Pool
    ...    ${IP_POOL_NAME}
    ...    ${IP_POOL_SUBNET}
    ...    ${IP_POOL_START}
    ...    ${IP_POOL_END}
    ...    ${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
    Rancher - Create Image    ${IMAGE_NAME}    ${UBUNTU_IMAGE_URL}
    Rancher - Wait For Image Ready    ${IMAGE_NAME}    ${WAIT_TIMEOUT}

    Log    Test environment ready (version: ${RKE2_VERSION}, timestamp: ${timestamp})    console=yes

Import Harvester To Rancher In Setup
    [Documentation]    Import Harvester into Rancher during suite setup.
    Log    Creating Harvester management cluster: ${HARVESTER_CLUSTER_NAME}

    Rancher - Create Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}

    ${cluster}=    Rancher - Wait For Cluster ID    ${HARVESTER_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Set Suite Variable    ${HARVESTER_CLUSTER_ID}    ${cluster_id}
    Log    Harvester cluster ID: ${cluster_id}

    ${manifest_url}=    Rancher - Get Cluster Registration URL
    ...    ${cluster_id}    ${RANCHER_ENDPOINT}    ${RANCHER_WAIT_TIMEOUT}
    Should Not Be Empty    ${manifest_url}    Registration URL not found

    Rancher - Set Cluster Registration URL    ${manifest_url}

    Rancher - Wait For Harvester Ready    ${HARVESTER_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Log    Harvester imported successfully: ${HARVESTER_CLUSTER_NAME}

Suite Teardown For Rancher Integration Tests
    [Documentation]    Cleanup all resources after tests.
    Log    Running suite teardown

    # Cleanup clusters (best effort)
    Run Keyword And Ignore Error    Cleanup Cluster By Name    ${SINGLE_CLUSTER_NAME}
    Run Keyword And Ignore Error    Cleanup Cluster By Name    ${MULTI_CLUSTER_NAME}

    # Delete cloud credential
    Run Keyword If    '${CLOUD_CREDENTIAL_ID}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Rancher - Delete Cloud Credential    ${CLOUD_CREDENTIAL_ID}

    # Delete Harvester mgmt cluster
    Run Keyword And Ignore Error    Rancher - Delete Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}

    # Delete shared resources
    Run Keyword And Ignore Error    Rancher - Delete IP Pool    ${IP_POOL_NAME}
    Run Keyword And Ignore Error    Rancher - Delete VLAN Network    ${VLAN_NETWORK_NAME}
    Run Keyword And Ignore Error    Rancher - Delete Image    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Rancher - Set Cluster Registration URL    ${EMPTY}

    Cleanup test resources
    Log    Suite teardown completed

# ============================================================
# Utility keywords
# ============================================================
Cleanup Cluster By Name
    [Arguments]    ${cluster_name}
    [Documentation]    Delete a specific RKE2 cluster by name (best effort).
    Run Keyword And Ignore Error    Rancher - Delete RKE2 Cluster    ${cluster_name}
    Run Keyword And Ignore Error    Rancher - Wait For RKE2 Cluster Deleted    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
