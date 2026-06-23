*** Settings ***
Documentation    Rancher Integration Keywords - Reusable keywords for Rancher operations
Library          ../libs/keywords/rancher_keywords.py
Library          Collections
Library          String
Resource         variables.resource
Resource         common.resource
Resource         storage_network.resource
Resource         network.resource
Resource         image.resource
Resource         virtualmachine.resource

*** Keywords ***
# State Management
Set State
    [Arguments]    ${key}    ${value}
    [Documentation]    Store state for later use between keywords
    Log    Setting state ${key} = ${value}
    rancher_keywords.set_state    ${key}    ${value}

Get State
    [Arguments]    ${key}    ${default}=${NONE}
    [Documentation]    Retrieve stored state
    ${value}=    rancher_keywords.get_state    ${key}    ${default}
    RETURN    ${value}

Clear State
    [Arguments]    ${key}=${NONE}
    [Documentation]    Clear state - either specific key or all
    rancher_keywords.clear_state    ${key}

Generate Unique Name
    [Arguments]    ${prefix}=test
    [Documentation]    Generate unique name with timestamp
    ${name}=    rancher_keywords.generate_unique_name    ${prefix}
    Log    Generated unique name: ${name}
    RETURN    ${name}

# Harvester Management Cluster Operations
Create Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Create Harvester management cluster entry in Rancher (Import Existing)
    ...               Args:
    ...                   cluster_name: Name of the cluster entry to create
    ...               Returns:
    ...                   dict: Cluster data
    Log    Creating Harvester management cluster: ${cluster_name}
    ${cluster}=    rancher_keywords.create_harvester_mgmt_cluster    ${cluster_name}
    RETURN    ${cluster}

Get Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Get Harvester management cluster details
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...               Returns:
    ...                   dict: Cluster data or None if not found
    ${cluster}=    rancher_keywords.get_harvester_mgmt_cluster    ${cluster_name}
    RETURN    ${cluster}

Delete Harvester Mgmt Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Delete Harvester management cluster entry
    ...               Args:
    ...                   cluster_name: Name of the cluster to delete
    Log    Deleting Harvester management cluster: ${cluster_name}
    rancher_keywords.delete_harvester_mgmt_cluster    ${cluster_name}

Wait For Cluster ID
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for cluster to get its internal ID (status.clusterName)
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Cluster data with ID
    Log    Waiting for cluster ${cluster_name} to get cluster ID
    ${cluster}=    rancher_keywords.wait_for_cluster_id    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

Wait For Harvester Ready
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for Harvester cluster to be ready in Rancher
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds (default: WAIT_TIMEOUT)
    ...               Returns:
    ...                   dict: Cluster data when ready
    Log    Waiting for Harvester cluster ${cluster_name} to be ready
    ${cluster}=    rancher_keywords.wait_for_harvester_ready    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

# Import Harvester Operations
Get Cluster Registration URL
    [Arguments]    ${cluster_id}    ${rancher_endpoint}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Get cluster registration URL for importing Harvester
    ...               Args:
    ...                   cluster_id: Internal cluster ID (e.g. c-m-xxxxx)
    ...                   rancher_endpoint: Rancher server endpoint
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   str: Registration manifest URL
    ${url}=    rancher_keywords.get_cluster_registration_url    ${cluster_id}    ${rancher_endpoint}    ${timeout}
    Log    Registration URL: ${url}
    RETURN    ${url}

Set Cluster Registration URL
    [Arguments]    ${url}
    [Documentation]    Set cluster-registration-url setting in Harvester
    ...               Args:
    ...                   url: Registration URL to set
    Log    Setting cluster-registration-url
    rancher_keywords.set_cluster_registration_url    ${url}

Get All RKE2 Versions
    [Arguments]    ${rancher_endpoint}    ${max_versions}=${NONE}
    [Documentation]    Get all available RKE2 versions from Rancher
    ...               Args:
    ...                   rancher_endpoint: Rancher server endpoint
    ...                   max_versions: Maximum number of versions to return (None = all)
    ...               Returns:
    ...                   list: List of RKE2 version strings sorted newest first
    Log    Getting all RKE2 versions from Rancher
    ${versions}=    rancher_keywords.get_all_rke2_versions    ${rancher_endpoint}    ${max_versions}
    RETURN    ${versions}

Resolve RKE2 Versions
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
    ${versions}=    rancher_keywords.resolve_rke2_versions    ${versions_input}    ${rancher_endpoint}    ${max_versions}
    RETURN    ${versions}

Get RKE2 Version
    [Arguments]    ${target_version}    ${rancher_endpoint}
    [Documentation]    Get RKE2 version from Rancher that matches target version
    ...               Args:
    ...                   target_version: Target version prefix (e.g. 'v1.28')
    ...                   rancher_endpoint: Rancher server endpoint
    ...               Returns:
    ...                   str: Full RKE2 version (e.g. 'v1.28.15+rke2r1')
    Log    Getting RKE2 version for target: ${target_version}
    ${version}=    rancher_keywords.get_rke2_version    ${target_version}    ${rancher_endpoint}
    RETURN    ${version}

Import Harvester To Rancher
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Full workflow to import Harvester to Rancher
    ...               Args:
    ...                   cluster_name: Name for the Harvester entry in Rancher
    ...                   timeout: Timeout for the import operation
    ...               Returns:
    ...                   dict: Harvester cluster data
    Log    Importing Harvester to Rancher as: ${cluster_name}
    ${cluster}=    rancher_keywords.import_harvester_to_rancher    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

# Cloud Credential Operations
Create Cloud Credential
    [Arguments]    ${name}    ${kubeconfig}    ${cluster_id}
    [Documentation]    Create cloud credential for Harvester
    ...               Args:
    ...                   name: Name for the credential
    ...                   kubeconfig: Kubeconfig content
    ...                   cluster_id: Harvester cluster ID
    ...               Returns:
    ...                   dict: Credential data
    Log    Creating cloud credential: ${name}
    ${credential}=    rancher_keywords.create_cloud_credential    ${name}    ${kubeconfig}    ${cluster_id}
    RETURN    ${credential}

Delete Cloud Credential
    [Arguments]    ${credential_id}
    [Documentation]    Delete cloud credential
    ...               Args:
    ...                   credential_id: ID of the credential to delete
    Log    Deleting cloud credential: ${credential_id}
    rancher_keywords.delete_cloud_credential    ${credential_id}

# RKE2 Cluster Operations
Create RKE2 Cluster
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
    ${cluster}=    rancher_keywords.create_rke2_cluster    ${name}    ${cloud_provider_config_id}
    ...            ${hostname_prefix}    ${harvester_config_name}    ${k8s_version}
    ...            ${cloud_credential_id}    ${quantity}    ${ingress}
    RETURN    ${cluster}

Get RKE2 Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Get RKE2 cluster details
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...               Returns:
    ...                   dict: Cluster data or None if not found
    ${cluster}=    rancher_keywords.get_rke2_cluster    ${cluster_name}
    RETURN    ${cluster}

Delete RKE2 Cluster
    [Arguments]    ${cluster_name}
    [Documentation]    Delete RKE2 cluster
    ...               Args:
    ...                   cluster_name: Name of the cluster to delete
    Log    Deleting RKE2 cluster: ${cluster_name}
    rancher_keywords.delete_rke2_cluster    ${cluster_name}

Wait For RKE2 Cluster Ready
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for RKE2 cluster to be ready
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Cluster data when ready
    Log    Waiting for RKE2 cluster ${cluster_name} to be ready
    ${cluster}=    rancher_keywords.wait_for_rke2_cluster_ready    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

Wait For RKE2 Cluster Deleted
    [Arguments]    ${cluster_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for RKE2 cluster to be deleted
    ...               Args:
    ...                   cluster_name: Name of the cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   bool: True when deleted
    Log    Waiting for RKE2 cluster ${cluster_name} to be deleted
    ${result}=    rancher_keywords.wait_for_rke2_cluster_deleted    ${cluster_name}    ${timeout}
    RETURN    ${result}

Scale RKE2 Cluster
    [Arguments]    ${cluster_name}    ${worker_count}    ${harvester_config_name}
    [Documentation]    Scale RKE2 cluster by adding/removing a worker-only machine pool.
    ...               Args:
    ...                   cluster_name: Name of the RKE2 cluster
    ...                   worker_count: Number of worker nodes (0 to remove worker pool)
    ...                   harvester_config_name: HarvesterConfig name for worker pool nodes
    Log    Scaling RKE2 cluster ${cluster_name}: worker_count=${worker_count}
    rancher_keywords.scale_rke2_cluster    ${cluster_name}    ${worker_count}    ${harvester_config_name}

Upgrade RKE2 Cluster
    [Arguments]    ${cluster_name}    ${new_k8s_version}
    [Documentation]    Upgrade RKE2 cluster to a new Kubernetes version.
    ...               Args:
    ...                   cluster_name: Name of the RKE2 cluster
    ...                   new_k8s_version: Target Kubernetes version string
    Log    Upgrading RKE2 cluster ${cluster_name} to ${new_k8s_version}
    rancher_keywords.upgrade_rke2_cluster    ${cluster_name}    ${new_k8s_version}

Get Next RKE2 Version
    [Arguments]    ${current_version}    ${rancher_endpoint}
    [Documentation]    Get the next (n+1) RKE2 version available on Rancher
    ...               for the same minor stream.
    ...               Args:
    ...                   current_version: Current RKE2 version (e.g. v1.31.4+rke2r1)
    ...                   rancher_endpoint: Rancher server endpoint
    ...               Returns:
    ...                   str: Next version string, or empty string if none available
    ${version}=    rancher_keywords.get_next_rke2_version    ${current_version}    ${rancher_endpoint}
    RETURN    ${version}

Configure KDM If Custom
    [Documentation]    If KDM_URL is not 'default', update the Rancher global setting
    ...               rke-metadata-config to use the given URL and set refresh-interval-minutes to 0.
    ...               This allows custom KDM data.json files to provide RKE2 versions (e.g. rc builds).
    ...               No action is taken when KDM_URL is 'default'.
    IF    '${KDM_URL}' != 'default'
        Log    Configuring KDM URL: ${KDM_URL}    console=yes
        rancher_keywords.configure_kdm_url    ${KDM_URL}
        Log    KDM configured. Rancher will use ${KDM_URL} with refresh-interval-minutes=0    console=yes
        Wait For KDM Refresh    ${RKE2_VERSION}
    ELSE
        Log    KDM_URL is 'default' - keeping existing Rancher rke-metadata-config    console=yes
    END

Wait For KDM Refresh
    [Arguments]    ${version_prefix}    ${timeout}=${RANCHER_WAIT_TIMEOUT}    ${interval}=${RETRY_INTERVAL}
    [Documentation]    Wait until Rancher's version list contains an RKE2 version
    ...               matching ${version_prefix}. This ensures the custom KDM
    ...               data.json has been fetched and processed before cluster
    ...               creation attempts to resolve versions.
    Log    Waiting for KDM refresh — expecting versions matching ${version_prefix}    console=yes
    Wait Until Keyword Succeeds    ${timeout}    ${interval}
    ...    KDM Has Versions For    ${version_prefix}

KDM Has Versions For
    [Arguments]    ${version_prefix}
    [Documentation]    Assert that Rancher exposes at least one RKE2 version starting with
    ...               ${version_prefix}. Fails if no match found yet; intended for use
    ...               with Wait Until Keyword Succeeds.
    ${versions}=    rancher_keywords.get_all_rke2_versions    ${RANCHER_ENDPOINT}
    ${matched}=    Evaluate    [v for v in ${versions} if v.startswith('${version_prefix}')]
    Should Not Be Empty    ${matched}    KDM has not yet exposed versions matching ${version_prefix}
    Log    KDM refreshed — found versions: ${matched}    console=yes

Verify LB Response
    [Arguments]    ${url}    ${expected_text}=${NONE}
    [Documentation]    Verify LoadBalancer is responding with expected content
    ...               Args:
    ...                   url: URL to query
    ...                   expected_text: Text expected in response (optional)
    ...               Returns:
    ...                   bool: True if response matches
    Log    Verifying LB response from: ${url}
    ${result}=    rancher_keywords.verify_lb_response    ${url}    ${expected_text}
    RETURN    ${result}

Verify LB Via Cluster
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
    ${result}=    rancher_keywords.verify_lb_via_cluster    ${cluster_id}    ${service_name}
    ...    ${port}    ${namespace}    ${expected_text}
    RETURN    ${result}

# Harvester Config Operations
Create Harvester Config
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
    ${config}=    rancher_keywords.create_harvester_config    ${name}    ${cpus}    ${mems}    ${disks}
    ...           ${image_id}    ${network_id}    ${ssh_user}    ${user_data}
    RETURN    ${config}

# Kubeconfig Operations
Generate Kubeconfig
    [Arguments]    ${cluster_id}    ${cluster_name}
    [Documentation]    Generate full-access kubeconfig for a cluster (for cloud credentials)
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   cluster_name: Cluster name
    ...               Returns:
    ...                   str: Kubeconfig content
    Log    Generating kubeconfig for cluster: ${cluster_name}
    ${kubeconfig}=    rancher_keywords.generate_kubeconfig    ${cluster_id}    ${cluster_name}
    RETURN    ${kubeconfig}

Generate Cloud Provider Kubeconfig
    [Arguments]    ${cluster_id}    ${cluster_name}
    [Documentation]    Generate cloud provider kubeconfig with external URL
    ...               (for cloud provider secret inside guest VM)
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   cluster_name: Cluster name
    ...               Returns:
    ...                   str: Kubeconfig content with external Rancher URL
    Log    Generating cloud provider kubeconfig for cluster: ${cluster_name}
    ${kubeconfig}=    rancher_keywords.generate_cloud_provider_kubeconfig    ${cluster_id}    ${cluster_name}
    RETURN    ${kubeconfig}

# Secret Operations
Create Cloud Provider Secret
    [Arguments]    ${name}    ${kubeconfig}    ${cluster_name}
    [Documentation]    Create secret for cloud provider config
    ...               Args:
    ...                   name: Secret name
    ...                   kubeconfig: Kubeconfig content
    ...                   cluster_name: Cluster name for annotations
    ...               Returns:
    ...                   dict: Secret data
    Log    Creating cloud provider secret: ${name}
    ${secret}=    rancher_keywords.create_cloud_provider_secret    ${name}    ${kubeconfig}    ${cluster_name}
    RETURN    ${secret}

# Deployment Operations
Create Deployment
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
    ${deployment}=    rancher_keywords.create_deployment    ${cluster_id}    ${namespace}    ${name}    ${image}    ${pvc}
    RETURN    ${deployment}

Delete Deployment
    [Arguments]    ${cluster_id}    ${namespace}    ${name}
    [Documentation]    Delete deployment from guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    Log    Deleting deployment ${name} from cluster ${cluster_id}
    rancher_keywords.delete_deployment    ${cluster_id}    ${namespace}    ${name}

Wait For Deployment Ready
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
    ${deployment}=    rancher_keywords.wait_for_deployment_ready    ${cluster_id}    ${namespace}    ${name}    ${timeout}
    RETURN    ${deployment}

Wait For Deployment Deleted
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
    ${result}=    rancher_keywords.wait_for_deployment_deleted    ${cluster_id}    ${namespace}    ${name}    ${timeout}
    RETURN    ${result}

# PVC Operations
Create PVC
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
    ${pvc}=    rancher_keywords.create_pvc    ${cluster_id}    ${name}    ${size}    ${storage_class}
    RETURN    ${pvc}

Delete PVC
    [Arguments]    ${cluster_id}    ${name}
    [Documentation]    Delete PVC from guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    Log    Deleting PVC ${name} from cluster ${cluster_id}
    rancher_keywords.delete_pvc    ${cluster_id}    ${name}

Wait For PVC Bound
    [Arguments]    ${cluster_id}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for PVC to be bound
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: PVC data when bound
    Log    Waiting for PVC ${name} to be bound
    ${pvc}=    rancher_keywords.wait_for_pvc_bound    ${cluster_id}    ${name}    ${timeout}
    RETURN    ${pvc}

# Load Balancer Service Operations
Create LB Service
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
    ${service}=    rancher_keywords.create_lb_service    ${cluster_id}    ${namespace}    ${name}
    ...            ${target_deployment}    ${port}    ${target_port}    ${ipam}
    RETURN    ${service}

Delete LB Service
    [Arguments]    ${cluster_id}    ${name}
    [Documentation]    Delete LoadBalancer service
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: Service name
    Log    Deleting LoadBalancer service ${name} from cluster ${cluster_id}
    rancher_keywords.delete_lb_service    ${cluster_id}    ${name}

Wait For LB Service Ready
    [Arguments]    ${cluster_id}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for LoadBalancer service to be ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: Service name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Service data when ready
    Log    Waiting for LoadBalancer service ${name} to be ready
    ${service}=    rancher_keywords.wait_for_lb_service_ready    ${cluster_id}    ${name}    ${timeout}
    RETURN    ${service}

Query LB Service
    [Arguments]    ${url}
    [Documentation]    Query LoadBalancer service endpoint
    ...               Args:
    ...                   url: URL to query
    ...               Returns:
    ...                   tuple: (status_code, response_text)
    Log    Querying LoadBalancer service at: ${url}
    ${code}    ${text}=    rancher_keywords.query_lb_service    ${url}
    RETURN    ${code}    ${text}

Verify LB Nginx Response
    [Arguments]    ${url}
    [Documentation]    Verify LoadBalancer returns nginx welcome page
    ...               Args:
    ...                   url: URL to query
    ...               Returns:
    ...                   bool: True if nginx welcome page found
    Log    Verifying nginx response from: ${url}
    ${result}=    rancher_keywords.verify_lb_nginx_response    ${url}
    RETURN    ${result}

# Harvester Deployments Check
Wait For Harvester Deployments Ready
    [Arguments]    ${cluster_id}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for harvester-cloud-provider and harvester-csi-driver to be ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   timeout: Timeout in seconds
    Log    Waiting for Harvester deployments in cluster ${cluster_id}
    rancher_keywords.wait_for_harvester_deployments_ready    ${cluster_id}    ${timeout}

# Cluster Network Operations (delegated to network module)
Create Cluster Network
    [Arguments]    ${name}
    [Documentation]    Create cluster network (delegates to Network module)
    ${cn}=    network.Create Cluster Network    ${name}
    RETURN    ${cn}

Delete Cluster Network
    [Arguments]    ${name}
    [Documentation]    Delete cluster network (delegates to Network module)
    network.Delete Cluster Network    ${name}

Create VLAN Config
    [Arguments]    ${name}    ${cluster_network}    ${nic}
    [Documentation]    Create VLAN config (delegates to Network module)
    ${vc}=    network.Create VLAN Config    ${name}    ${cluster_network}    ${nic}
    RETURN    ${vc}

Delete VLAN Config
    [Arguments]    ${name}
    [Documentation]    Delete VLAN config (delegates to Network module)
    network.Delete VLAN Config    ${name}

Wait For Cluster Network Ready
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for cluster network ready (delegates to Network module)
    ${cn}=    network.Wait For Cluster Network Ready    ${name}    ${timeout}
    RETURN    ${cn}

# VLAN Network Operations (delegated to network module)
Create VLAN Network
    [Arguments]    ${name}    ${vlan_id}    ${cluster_network}
    [Documentation]    Create VLAN network (delegates to Network module)
    ${network}=    network.Create VLAN Network    ${name}    ${vlan_id}    ${cluster_network}
    RETURN    ${network}

Delete VLAN Network
    [Arguments]    ${name}
    [Documentation]    Delete VLAN network (delegates to Network module)
    network.Delete VLAN Network    ${name}

# IP Pool Operations (delegated to network module)
Get IP Pool
    [Arguments]    ${name}
    [Documentation]    Get IP pool (delegates to Network module)
    ${pool}=    network.Get IP Pool    ${name}
    RETURN    ${pool}

Create IP Pool
    [Arguments]    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}    ${gateway}
    [Documentation]    Create IP pool (delegates to Network module)
    ${pool}=    network.Create IP Pool    ${name}    ${subnet}    ${start_ip}    ${end_ip}    ${network_id}    ${gateway}
    RETURN    ${pool}

Delete IP Pool
    [Arguments]    ${name}
    [Documentation]    Delete IP pool (delegates to Network module)
    network.Delete IP Pool    ${name}

# Image Operations (delegated to Image module)
Create Image
    [Arguments]    ${name}    ${url}
    [Documentation]    Create image by URL (delegates to Image module)
    image.Create image from url with name    ${name}    ${url}

Wait For Image Ready
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for image ready (delegates to Image module)
    image.Wait for image downloaded by name    ${name}    ${timeout}

Delete Image
    [Arguments]    ${name}
    [Documentation]    Delete image (delegates to Image module)
    image.Delete image by name    ${name}

# Custom RKE2 Cluster Operations
Create Custom RKE2 Cluster
    [Arguments]    ${name}    ${cloud_provider_config_id}    ${k8s_version}
    ...            ${cloud_credential_id}    ${ingress}=${INGRESS_CONTROLLER}
    [Documentation]    Create a custom RKE2 cluster without machinePools.
    ...               Nodes are registered externally. The Harvester cloud
    ...               provider is configured.
    ...               Args:
    ...                   name: Cluster name
    ...                   cloud_provider_config_id: Cloud provider config secret ID
    ...                   k8s_version: Kubernetes version
    ...                   cloud_credential_id: Cloud credential ID
    ...                   ingress: Ingress controller (default: INGRESS_CONTROLLER)
    ...               Returns:
    ...                   dict: Cluster data
    Log    Creating custom RKE2 cluster: ${name}
    ${cluster}=    rancher_keywords.create_custom_rke2_cluster    ${name}    ${cloud_provider_config_id}
    ...            ${k8s_version}    ${cloud_credential_id}    ${ingress}
    RETURN    ${cluster}

Update Cluster Chart Name
    [Arguments]    ${cluster_name}    ${mgmt_cluster_id}
    [Documentation]    Patch the cloud provider clusterName in a custom cluster's
    ...               chartValues with the real management cluster ID.
    ...               Args:
    ...                   cluster_name: Provisioning cluster name
    ...                   mgmt_cluster_id: Management cluster ID (e.g. c-m-xxxxx)
    Log    Updating chart clusterName to ${mgmt_cluster_id} for ${cluster_name}
    rancher_keywords.update_cluster_chart_name    ${cluster_name}    ${mgmt_cluster_id}

Fix Cloud Provider Cluster Name
    [Arguments]    ${cluster_id}
    [Documentation]    Fix the cloud-provider --cluster-name arg on the guest cluster.
    ...               Rancher deploys the chart with the provisioning name, but
    ...               the cloud provider needs the management cluster ID to match
    ...               VMs. Patches the deployment and waits for rollout.
    ...               Args:
    ...                   cluster_id: Management cluster ID (e.g. c-m-xxxxx)
    Log    Fixing cloud provider clusterName on cluster ${cluster_id}    console=yes
    rancher_keywords.fix_cloud_provider_cluster_name    ${cluster_id}

Get Cluster Registration Command
    [Arguments]    ${cluster_name}    ${timeout}=${RANCHER_WAIT_TIMEOUT}
    [Documentation]    Get the insecure node registration command for a custom cluster.
    ...               Args:
    ...                   cluster_name: Name of the provisioning cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   str: The insecure node command to run on VMs
    Log    Getting registration command for: ${cluster_name}
    ${command}=    rancher_keywords.get_cluster_registration_command    ${cluster_name}    ${timeout}
    RETURN    ${command}

# Harvester VM Operations (for custom cluster nodes)
Create Harvester VM
    [Arguments]    ${name}    ${image_id}    ${network_id}    ${cpus}=2    ${memory}=4
    ...            ${disk_size}=40    ${ssh_user}=ubuntu    ${user_data}=${EMPTY}
    ...            ${network_data}=${EMPTY}    ${guest_cluster_id}=${EMPTY}
    [Documentation]    Create a VM on Harvester for custom cluster nodes.
    ...               Args:
    ...                   name: VM name
    ...                   image_id: Image ID (namespace/name format)
    ...                   network_id: Network ID (namespace/name format)
    ...                   cpus: Number of CPU cores (default: 2)
    ...                   memory: Memory in GiB (default: 4)
    ...                   disk_size: Disk size in GiB (default: 40)
    ...                   ssh_user: SSH username (default: ubuntu)
    ...                   user_data: Cloud-init user data string
    ...                   network_data: Cloud-init network data string (v2 format)
    ...                   guest_cluster_id: Management cluster ID (c-m-xxxxx) for LB labels
    ...               Returns:
    ...                   dict: VM data
    Log    Creating Harvester VM: ${name}
    ${vm}=    rancher_keywords.create_harvester_vm    ${name}    ${image_id}    ${network_id}
    ...       ${cpus}    ${memory}    ${disk_size}    ${ssh_user}    ${user_data}
    ...       ${network_data}    ${guest_cluster_id}
    RETURN    ${vm}

Wait For Harvester VM Ready
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for a Harvester VM to be running.
    vm_keywords.wait_for_vm_running    ${name}    ${timeout}

Delete Harvester VM
    [Arguments]    ${name}
    [Documentation]    Delete a Harvester VM.
    vm_keywords.delete_vm    ${name}

Wait For Harvester VM Deleted
    [Arguments]    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for a Harvester VM to be fully removed.
    vm_keywords.wait_for_vm_deleted    ${name}    ${timeout}

# Chart Install Operations
Install Chart
    [Arguments]    ${cluster_id}    ${repo_name}    ${chart_name}    ${version}
    ...            ${release_name}    ${namespace}    ${values}=${None}
    [Documentation]    Install a Helm chart on a guest cluster via Rancher catalog API.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   repo_name: Chart repository name
    ...                   chart_name: Chart name
    ...                   version: Chart version (empty string for latest)
    ...                   release_name: Helm release name
    ...                   namespace: Target namespace
    ...                   values: Optional dict of chart values overrides
    Log    Installing chart ${chart_name} v${version} on cluster ${cluster_id}
    ${result}=    rancher_keywords.install_chart    ${cluster_id}    ${repo_name}    ${chart_name}
    ...    ${version}    ${release_name}    ${namespace}    ${values}
    RETURN    ${result}

Get Chart Versions
    [Arguments]    ${repo_name}    ${chart_name}    ${cluster_id}=${None}
    [Documentation]    Get available versions for a chart from a Rancher chart repo.
    ...               Args:
    ...                   repo_name: Chart repository name
    ...                   chart_name: Chart name
    ...                   cluster_id: Optional guest cluster ID to query via proxy
    ${versions}=    rancher_keywords.get_chart_versions    ${repo_name}    ${chart_name}    ${cluster_id}
    RETURN    ${versions}

Create Cluster Repo
    [Arguments]    ${cluster_id}    ${repo_name}    ${git_url}    ${git_branch}
    [Documentation]    Create a ClusterRepo on a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   repo_name: Name for the ClusterRepo resource
    ...                   git_url: Git repository URL
    ...                   git_branch: Git branch name
    Log    Creating ClusterRepo ${repo_name} (branch=${git_branch}) on cluster ${cluster_id}
    ${result}=    rancher_keywords.create_cluster_repo    ${cluster_id}    ${repo_name}    ${git_url}    ${git_branch}
    RETURN    ${result}

Wait For Cluster Repo Ready
    [Arguments]    ${cluster_id}    ${repo_name}    ${timeout}=${RANCHER_WAIT_TIMEOUT}
    ...            ${expected_git_branch}=${NONE}
    [Documentation]    Wait for a ClusterRepo to finish downloading on a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   repo_name: ClusterRepo name
    ...                   timeout: Timeout in seconds
    ...                   expected_git_branch: When set, verify spec.gitBranch matches
    Log    Waiting for ClusterRepo ${repo_name} to be ready
    ${result}=    rancher_keywords.wait_for_cluster_repo_ready    ${cluster_id}    ${repo_name}
    ...    ${timeout}    ${expected_git_branch}
    RETURN    ${result}

Create Cloud Config Secret
    [Arguments]    ${cluster_id}    ${secret_name}    ${namespace}    ${kubeconfig}
    [Documentation]    Create a cloud-provider-config secret on a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   secret_name: Secret name
    ...                   namespace: Target namespace
    ...                   kubeconfig: Harvester cloud-provider kubeconfig content
    Log    Creating cloud config secret ${secret_name} on cluster ${cluster_id}
    ${result}=    rancher_keywords.create_cloud_config_secret    ${cluster_id}    ${secret_name}
    ...    ${namespace}    ${kubeconfig}
    RETURN    ${result}

Wait For Chart App Ready
    [Arguments]    ${cluster_id}    ${release_name}    ${namespace}
    ...            ${timeout}=${RANCHER_WAIT_TIMEOUT}    ${expected_version}=${NONE}
    [Documentation]    Wait for a chart app to be deployed and ready.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   release_name: Helm release name
    ...                   namespace: Namespace where chart was installed
    ...                   timeout: Timeout in seconds
    ...                   expected_version: When set, also wait for this chart version
    Log    Waiting for chart app ${release_name} to be ready
    ${result}=    rancher_keywords.wait_for_chart_app_ready    ${cluster_id}    ${release_name}
    ...    ${namespace}    ${timeout}    ${expected_version}
    RETURN    ${result}

Get Deployed Chart Version
    [Arguments]    ${cluster_id}    ${release_name}    ${namespace}
    [Documentation]    Return the deployed version of an installed chart app.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   release_name: Helm release name
    ...                   namespace: Namespace where chart was installed
    ...               Returns:
    ...                   str: Deployed chart version string
    ${version}=    rancher_keywords.get_deployed_chart_version    ${cluster_id}    ${release_name}    ${namespace}
    RETURN    ${version}

Upgrade Chart
    [Arguments]    ${cluster_id}    ${repo_name}    ${chart_name}    ${version}
    ...            ${release_name}    ${namespace}    ${values}=${None}
    [Documentation]    Upgrade an installed Helm chart on a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   repo_name: Chart repository name
    ...                   chart_name: Chart name
    ...                   version: Target chart version (empty string for latest)
    ...                   release_name: Helm release name
    ...                   namespace: Target namespace
    ...                   values: Optional dict of chart values overrides
    Log    Upgrading chart ${chart_name} to v${version} on cluster ${cluster_id}
    ${result}=    rancher_keywords.upgrade_chart    ${cluster_id}    ${repo_name}    ${chart_name}
    ...    ${version}    ${release_name}    ${namespace}    ${values}
    RETURN    ${result}

Uninstall Chart
    [Arguments]    ${cluster_id}    ${release_name}    ${namespace}
    [Documentation]    Uninstall a Helm chart (app) from a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   release_name: Helm release name
    ...                   namespace: Namespace where the chart is installed
    Log    Uninstalling chart ${release_name} from cluster ${cluster_id}
    ${result}=    rancher_keywords.uninstall_chart    ${cluster_id}    ${release_name}    ${namespace}
    RETURN    ${result}

Wait For Chart App Deleted
    [Arguments]    ${cluster_id}    ${release_name}    ${namespace}    ${timeout}=${RANCHER_WAIT_TIMEOUT}
    [Documentation]    Wait for a chart app to be fully removed from a guest cluster.
    ...               Args:
    ...                   cluster_id: Rancher management cluster ID
    ...                   release_name: Helm release name
    ...                   namespace: Namespace where chart was installed
    ...                   timeout: Timeout in seconds
    Log    Waiting for chart app ${release_name} to be deleted
    ${result}=    rancher_keywords.wait_for_chart_app_deleted    ${cluster_id}    ${release_name}
    ...    ${namespace}    ${timeout}
    RETURN    ${result}

Scale Deployment
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${replicas}
    [Documentation]    Scale a deployment in a guest cluster to the given replica count.
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    ...                   replicas: Desired replica count
    Log    Scaling deployment ${name} to ${replicas} replicas
    rancher_keywords.scale_deployment    ${cluster_id}    ${namespace}    ${name}    ${replicas}

Wait For Deployment Scaled
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${replicas}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for a deployment to reach the given ready replica count.
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: Deployment name
    ...                   replicas: Expected ready replica count
    ...                   timeout: Timeout in seconds
    Log    Waiting for deployment ${name} to scale to ${replicas}
    ${result}=    rancher_keywords.wait_for_deployment_scaled    ${cluster_id}    ${namespace}    ${name}
    ...    ${replicas}    ${timeout}
    RETURN    ${result}

# RWX Volume / StorageClass / StatefulSet Operations
Create RWX StorageClass On Host
    [Arguments]    ${name}=longhorn-rwx
    [Documentation]    Create an RWX-capable StorageClass on the host Harvester cluster.
    ...               Uses Longhorn provisioner with NFS options for ReadWriteMany support.
    ...               Args:
    ...                   name: StorageClass name (default: longhorn-rwx)
    ...               Returns:
    ...                   dict: StorageClass data
    Log    Creating RWX StorageClass on host: ${name}
    ${sc}=    rancher_keywords.create_rwx_storage_class_on_host    ${name}
    RETURN    ${sc}

Delete RWX StorageClass On Host
    [Arguments]    ${name}=longhorn-rwx
    [Documentation]    Delete the RWX StorageClass from the host Harvester cluster.
    ...               Args:
    ...                   name: StorageClass name (default: longhorn-rwx)
    Log    Deleting RWX StorageClass from host: ${name}
    rancher_keywords.delete_rwx_storage_class_on_host    ${name}

Create Guest StorageClass
    [Arguments]    ${cluster_id}    ${name}    ${host_storage_class}=longhorn-rwx
    [Documentation]    Create a StorageClass on the guest cluster referencing a host StorageClass.
    ...               Uses the Harvester CSI driver provisioner with hostStorageClass parameter.
    ...               Args:
    ...                   cluster_id: Guest cluster ID
    ...                   name: StorageClass name on the guest cluster
    ...                   host_storage_class: Name of the host-side StorageClass to reference
    ...               Returns:
    ...                   dict: StorageClass data
    Log    Creating guest StorageClass ${name} in cluster ${cluster_id}
    ${sc}=    rancher_keywords.create_guest_storage_class    ${cluster_id}    ${name}    ${host_storage_class}
    RETURN    ${sc}

Delete Guest StorageClass
    [Arguments]    ${cluster_id}    ${name}
    [Documentation]    Delete a StorageClass from the guest cluster.
    ...               Args:
    ...                   cluster_id: Guest cluster ID
    ...                   name: StorageClass name
    Log    Deleting guest StorageClass ${name} from cluster ${cluster_id}
    rancher_keywords.delete_guest_storage_class    ${cluster_id}    ${name}

Create PVC RWX
    [Arguments]    ${cluster_id}    ${name}    ${size}=1Gi    ${storage_class}=${NONE}
    [Documentation]    Create a ReadWriteMany PVC in guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   name: PVC name
    ...                   size: Storage size (default: 1Gi)
    ...                   storage_class: Storage class name (optional)
    ...               Returns:
    ...                   dict: PVC data
    Log    Creating RWX PVC ${name} in cluster ${cluster_id}
    ${pvc}=    rancher_keywords.create_pvc_rwx    ${cluster_id}    ${name}    ${size}    ${storage_class}
    RETURN    ${pvc}

Create StatefulSet
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${image}    ${pvc_name}
    ...            ${replicas}=2
    [Documentation]    Create a StatefulSet that mounts an existing PVC
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: StatefulSet name
    ...                   image: Container image
    ...                   pvc_name: Existing PVC name to mount
    ...                   replicas: Number of replicas (default: 2)
    ...               Returns:
    ...                   dict: StatefulSet data
    Log    Creating StatefulSet ${name} in cluster ${cluster_id}
    ${sts}=    rancher_keywords.create_statefulset    ${cluster_id}    ${namespace}    ${name}    ${image}    ${pvc_name}    ${replicas}
    RETURN    ${sts}

Delete StatefulSet
    [Arguments]    ${cluster_id}    ${namespace}    ${name}
    [Documentation]    Delete StatefulSet from guest cluster
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: StatefulSet name
    Log    Deleting StatefulSet ${name} from cluster ${cluster_id}
    rancher_keywords.delete_statefulset    ${cluster_id}    ${namespace}    ${name}

Wait For StatefulSet Ready
    [Arguments]    ${cluster_id}    ${namespace}    ${name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait for StatefulSet to have all replicas ready
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   name: StatefulSet name
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: StatefulSet data when ready
    Log    Waiting for StatefulSet ${name} to be ready
    ${sts}=    rancher_keywords.wait_for_statefulset_ready    ${cluster_id}    ${namespace}    ${name}    ${timeout}
    RETURN    ${sts}

Exec Command In Pod
    [Arguments]    ${cluster_id}    ${namespace}    ${pod_name}    @{command}
    [Documentation]    Execute a command inside a pod
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   pod_name: Pod name
    ...                   command: Command parts to execute
    ...               Returns:
    ...                   str: Command stdout
    Log    Executing command in pod ${pod_name}
    ${output}=    rancher_keywords.exec_command_in_pod    ${cluster_id}    ${namespace}    ${pod_name}    ${command}
    RETURN    ${output}

Get Pods By Label
    [Arguments]    ${cluster_id}    ${namespace}    ${label_selector}
    [Documentation]    Get pods matching a label selector
    ...               Args:
    ...                   cluster_id: Cluster ID
    ...                   namespace: Namespace
    ...                   label_selector: Label selector string (e.g. 'name=myapp')
    ...               Returns:
    ...                   list: List of pod dicts
    Log    Getting pods with label ${label_selector} in cluster ${cluster_id}
    ${pods}=    rancher_keywords.get_pods_by_label    ${cluster_id}    ${namespace}    ${label_selector}
    RETURN    ${pods}

# Storage Network Operations (delegated to storage_network.resource)
Enable Storage Network
    [Arguments]    ${vlan_id}    ${cluster_network}    ${ip_range}    ${share_rwx}=${FALSE}
    [Documentation]    Enable the storage-network Harvester setting.
    ...               Delegates to Storage Network module.
    storage_network.Enable    ${vlan_id}    ${cluster_network}    ${ip_range}    ${share_rwx}

Disable Storage Network
    [Documentation]    Disable the storage-network Harvester setting.
    ...               Delegates to Storage Network module.
    storage_network.Disable

Get Storage Network Status
    [Documentation]    Get the current storage-network setting status.
    ...               Delegates to Storage Network module.
    ${status}=    storage_network.Get Status
    RETURN    ${status}

Wait For Storage Network Ready
    [Arguments]    ${timeout}=${RANCHER_WAIT_TIMEOUT}
    [Documentation]    Wait for storage-network to be applied and completed.
    ...               Delegates to Storage Network module.
    ${data}=    storage_network.Wait For Ready    ${timeout}
    RETURN    ${data}

Get Vlan Network CIDR
    [Arguments]    ${vlan_id}    ${cluster_network}
    [Documentation]    Get the CIDR for a VLAN network by creating a temp network.
    ...               Delegates to Storage Network module.
    ${cidr}=    storage_network.Get Vlan Network CIDR    ${vlan_id}    ${cluster_network}
    RETURN    ${cidr}

Enable Longhorn RWX Storage Network
    [Documentation]    Set the Longhorn endpoint-network-for-rwx-volume setting.
    ...               Uses the same NAD as Longhorn's storage-network (read dynamically).
    ...               Delegates to Storage Network module.
    storage_network.Enable Longhorn RWX

Disable Longhorn RWX Storage Network
    [Documentation]    Clear the Longhorn endpoint-network-for-rwx-volume setting.
    ...               Delegates to Storage Network module.
    storage_network.Disable Longhorn RWX

# Import Existing Cluster Operations
Create Import Cluster
    [Arguments]    ${name}
    [Documentation]    Create a minimal provisioning cluster for importing an
    ...               existing cluster. The cluster has an empty spec; the actual
    ...               RKE2 cluster is running externally.
    ...               Args:
    ...                   name: Cluster name
    ...               Returns:
    ...                   dict: Cluster data
    Log    Creating import cluster: ${name}
    ${cluster}=    rancher_keywords.create_import_cluster    ${name}
    RETURN    ${cluster}

Wait For Import Cluster Ready
    [Arguments]    ${cluster_name}    ${timeout}=${RANCHER_WAIT_TIMEOUT}
    [Documentation]    Wait for an imported cluster to become active in Rancher.
    ...               Does not check machinePools or cluster.x-k8s.io machines.
    ...               Args:
    ...                   cluster_name: Name of the provisioning cluster
    ...                   timeout: Timeout in seconds
    ...               Returns:
    ...                   dict: Cluster data when ready
    Log    Waiting for import cluster ${cluster_name} to be ready
    ${cluster}=    rancher_keywords.wait_for_import_cluster_ready    ${cluster_name}    ${timeout}
    RETURN    ${cluster}

# ============================================================
# BDD Keywords - Given (Preconditions)
# ============================================================
Single node cluster is available
    [Documentation]    Verify single-node cluster exists before proceeding.
    Skip If    '${SINGLE_CLUSTER_ID}' == ''    Single-node cluster not available

Multi node cluster is available
    [Documentation]    Verify multi-node cluster exists before proceeding.
    Skip If    '${MULTI_CLUSTER_ID}' == ''    Multi-node cluster not available

Import cluster should be ready
    [Documentation]    Skip the Rancher Apps chart tests if the imported cluster did not come up.
    Skip If    not ${IMPORT_CLUSTER_READY}    Import cluster did not come up; skipping chart validation
    Skip If    '${IMPORT_CLUSTER_ID}' == ''    Import cluster ID not available; skipping chart validation

Next RKE2 version is available
    [Documentation]    Check if a newer RKE2 patch version exists on Rancher.
    ${next_version}=    Get Next RKE2 Version    ${RKE2_VERSION}    ${RANCHER_ENDPOINT}
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

Single node custom RKE2 cluster is created
    [Documentation]    Create a single-node custom RKE2 cluster with Harvester cloud
    ...               provider and store its ID. Nodes are registered via cloud-init.
    Log    Creating custom cluster: ${CUSTOM_CLUSTER_NAME}    console=yes
    ${cluster_id}=    Create Custom RKE2 Cluster With Full Setup
    ...    ${CUSTOM_CLUSTER_NAME}    ${RKE2_VERSION}    1
    Set Suite Variable    ${CUSTOM_CLUSTER_ID}    ${cluster_id}
    Log    Custom cluster created: ${CUSTOM_CLUSTER_NAME} (${cluster_id})    console=yes

Basic workloads are deployed on single node cluster
    [Documentation]    Deploy CSI, Whoami, and LB services on the single-node cluster.
    # CSI workload
    ${pvc_name}=    Set Variable    pvc-${SINGLE_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${SINGLE_CLUSTER_NAME}
    Create PVC    ${SINGLE_CLUSTER_ID}    ${pvc_name}    1Gi
    Create Deployment    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    nginx:1.27    ${pvc_name}
    # Whoami workload
    ${whoami_deploy}=    Set Variable    whoami-${SINGLE_CLUSTER_NAME}
    Create Deployment    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    traefik/whoami:v1.11.0
    # LB DHCP
    ${lb_dhcp}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-dhcp
    Create LB Service    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_dhcp}    ${whoami_deploy}    ipam=dhcp
    Wait For LB Service Ready    ${SINGLE_CLUSTER_ID}    ${lb_dhcp}
    # LB Pool
    ${lb_pool}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-pool
    Create LB Service    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_pool}    ${whoami_deploy}    ipam=pool
    Wait For LB Service Ready    ${SINGLE_CLUSTER_ID}    ${lb_pool}

Basic workloads are deployed on single node custom cluster
    [Documentation]    Deploy CSI, Whoami, and LB services on the custom cluster.
    # CSI workload
    ${pvc_name}=    Set Variable    pvc-${CUSTOM_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${CUSTOM_CLUSTER_NAME}
    Create PVC    ${CUSTOM_CLUSTER_ID}    ${pvc_name}    1Gi
    Create Deployment    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    nginx:1.27    ${pvc_name}
    # Whoami workload
    ${whoami_deploy}=    Set Variable    whoami-${CUSTOM_CLUSTER_NAME}
    Create Deployment    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    traefik/whoami:v1.11.0
    # LB DHCP
    ${lb_dhcp}=    Set Variable    lb-${CUSTOM_CLUSTER_NAME}-dhcp
    Create LB Service    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_dhcp}    ${whoami_deploy}    ipam=dhcp
    Wait For LB Service Ready    ${CUSTOM_CLUSTER_ID}    ${lb_dhcp}
    # LB Pool
    ${lb_pool}=    Set Variable    lb-${CUSTOM_CLUSTER_NAME}-pool
    Create LB Service    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_pool}    ${whoami_deploy}    ipam=pool
    Wait For LB Service Ready    ${CUSTOM_CLUSTER_ID}    ${lb_pool}

Multi node RKE2 cluster is created
    [Documentation]    Create a 3-node RKE2 cluster and store its ID.
    Log    Creating multi-node cluster: ${MULTI_CLUSTER_NAME}    console=yes
    ${cluster_id}=    Create RKE2 Cluster With Full Setup
    ...    ${MULTI_CLUSTER_NAME}    ${MULTI_CONFIG_NAME}    ${RKE2_VERSION}    3
    Set Suite Variable    ${MULTI_CLUSTER_ID}    ${cluster_id}
    Log    Multi-node cluster created: ${MULTI_CLUSTER_NAME} (${cluster_id})    console=yes

CSI workload with PVC is deployed
    [Documentation]    Create a PVC and nginx deployment using Harvester CSI.
    ${csi_ver}=    Get Deployed Chart Version
    ...    ${MULTI_CLUSTER_ID}    harvester-csi-driver    kube-system
    Log    Testing harvester-csi-driver version: ${csi_ver}    console=yes
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    Create PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}    1Gi
    Create Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}    nginx:1.27    ${pvc_name}

Whoami workload is deployed
    [Arguments]    ${suffix}
    [Documentation]    Deploy a Whoami workload for load balancer testing.
    ...               Args:
    ...                   suffix: Unique suffix to create multiple deployments
    ${deploy_name}=    Set Variable    whoami-${suffix}-${MULTI_CLUSTER_NAME}
    Create Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}    traefik/whoami:v1.11.0
    Append To List    ${WHOAMI_DEPLOYMENTS}    ${deploy_name}

Load balancer is created in DHCP mode
    [Arguments]    ${suffix}
    [Documentation]    Create a LoadBalancer service using DHCP for IP assignment.
    ...               Args:
    ...                   suffix: Suffix matching the Whoami deployment
    ${cp_ver}=    Get Deployed Chart Version
    ...    ${MULTI_CLUSTER_ID}    harvester-cloud-provider    kube-system
    Log    Testing harvester-cloud-provider version: ${cp_ver}    console=yes
    ${whoami_deploy}=    Set Variable    whoami-${suffix}-${MULTI_CLUSTER_NAME}
    ${lb_name}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-dhcp
    Create LB Service    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_name}    ${whoami_deploy}    ipam=dhcp
    Wait For LB Service Ready    ${MULTI_CLUSTER_ID}    ${lb_name}
    Set Suite Variable    ${LB_DHCP_NAME}    ${lb_name}

Load balancer is created in pool mode
    [Arguments]    ${suffix}
    [Documentation]    Create a LoadBalancer service using an IP pool for IP assignment.
    ...               Args:
    ...                   suffix: Suffix matching the Whoami deployment
    ${cp_ver}=    Get Deployed Chart Version
    ...    ${MULTI_CLUSTER_ID}    harvester-cloud-provider    kube-system
    Log    Testing harvester-cloud-provider version: ${cp_ver}    console=yes
    ${whoami_deploy}=    Set Variable    whoami-${suffix}-${MULTI_CLUSTER_NAME}
    ${lb_name}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-pool
    Create LB Service    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_name}    ${whoami_deploy}    ipam=pool
    Wait For LB Service Ready    ${MULTI_CLUSTER_ID}    ${lb_name}
    Set Suite Variable    ${LB_POOL_NAME}    ${lb_name}

Storage network is configured for RWX
    [Documentation]    Configure storage network with share-storage-network enabled.
    ...               Discovers CIDR from VLAN network, enables storage-network
    ...               setting in Harvester with share-storage-network: true,
    ...               which makes Harvester automatically configure Longhorn's
    ...               endpoint-network-for-rwx-volume setting.
    Log    Configuring storage network for RWX support    console=yes
    ${cluster_network}=    Set Variable    %{CLUSTER_NETWORK=mgmt}
    ${cidr}=    Get Vlan Network CIDR    ${VLAN_ID}    ${cluster_network}
    Enable Storage Network    ${VLAN_ID}    ${cluster_network}    ${cidr}    share_rwx=${TRUE}
    Wait For Storage Network Ready    ${RANCHER_WAIT_TIMEOUT}
    Log    Storage network configured for RWX    console=yes

Storage network is enabled for RWX
    [Documentation]    Stop all running VMs, enable storage network with
    ...               share-storage-network: true, then restart VMs.
    ...               Harvester automatically configures Longhorn's
    ...               endpoint-network-for-rwx-volume setting.
    Log    Enabling storage network for RWX    console=yes

    # Find and stop all VMs
    ${vm_names}=    List VMs by prefix    ${EMPTY}
    Log    Found VMs: ${vm_names}    console=yes
    FOR    ${vm_name}    IN    @{vm_names}
        VM is stopped    ${vm_name}
    END
    FOR    ${vm_name}    IN    @{vm_names}
        VM should be stopped    ${vm_name}
    END
    Log    All VMs stopped    console=yes

    # Enable storage network with RWX sharing
    ${cluster_network}=    Set Variable    %{CLUSTER_NETWORK=mgmt}
    ${cidr}=    Get Vlan Network CIDR    ${VLAN_ID}    ${cluster_network}
    Enable Storage Network    ${VLAN_ID}    ${cluster_network}    ${cidr}    share_rwx=${TRUE}
    Wait For Storage Network Ready    ${RANCHER_WAIT_TIMEOUT}
    Log    Storage network enabled    console=yes

    # Start VMs back up
    FOR    ${vm_name}    IN    @{vm_names}
        VM is started    ${vm_name}
    END
    FOR    ${vm_name}    IN    @{vm_names}
        VM should be running    ${vm_name}
    END
    Log    All VMs restarted    console=yes

Disable storage network for RWX
    [Documentation]    Stop all running VMs, disable storage network, then restart VMs.
    ...               Disabling storage-network automatically clears Longhorn's
    ...               endpoint-network-for-rwx-volume when share-storage-network was used.
    Log    Disabling storage network for RWX    console=yes

    # Find and stop all VMs
    ${vm_names}=    List VMs by prefix    ${EMPTY}
    FOR    ${vm_name}    IN    @{vm_names}
        Run Keyword And Ignore Error    VM is stopped    ${vm_name}
    END
    FOR    ${vm_name}    IN    @{vm_names}
        Run Keyword And Ignore Error    VM should be stopped    ${vm_name}
    END

    # Disable storage network settings
    Run Keyword And Ignore Error    Disable Storage Network

    # Restart VMs
    FOR    ${vm_name}    IN    @{vm_names}
        Run Keyword And Ignore Error    VM is started    ${vm_name}
    END
    FOR    ${vm_name}    IN    @{vm_names}
        Run Keyword And Ignore Error    VM should be running    ${vm_name}
    END
    Log    Storage network disabled and VMs restarted    console=yes

RWX volume is created on single node cluster
    [Documentation]    Create host RWX StorageClass, guest StorageClass referencing it,
    ...               and a ReadWriteMany PVC on the single-node cluster.
    ${host_sc}=    Set Variable    ${RWX_HOST_STORAGE_CLASS}
    ${guest_sc}=    Set Variable    rwx-guest-sc-${SINGLE_CLUSTER_NAME}
    ${pvc_name}=    Set Variable    pvc-rwx-${SINGLE_CLUSTER_NAME}
    Create RWX StorageClass On Host    ${host_sc}
    Create Guest StorageClass    ${SINGLE_CLUSTER_ID}    ${guest_sc}    ${host_sc}
    Create PVC RWX    ${SINGLE_CLUSTER_ID}    ${pvc_name}    1Gi    ${guest_sc}

RWX StatefulSet with 2 replicas is deployed on single node cluster
    [Documentation]    Create a StatefulSet with 2 replicas mounting the RWX PVC
    ...               on the single-node cluster.
    ${pvc_name}=    Set Variable    pvc-rwx-${SINGLE_CLUSTER_NAME}
    ${sts_name}=    Set Variable    rwx-sts-${SINGLE_CLUSTER_NAME}
    Create StatefulSet    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${sts_name}    busybox:stable    ${pvc_name}    2

RWX volume is created
    [Documentation]    Create host RWX StorageClass, guest StorageClass referencing it,
    ...               and a ReadWriteMany PVC using the guest StorageClass.
    ${host_sc}=    Set Variable    ${RWX_HOST_STORAGE_CLASS}
    ${guest_sc}=    Set Variable    rwx-guest-sc-${MULTI_CLUSTER_NAME}
    ${pvc_name}=    Set Variable    pvc-rwx-${MULTI_CLUSTER_NAME}
    Create RWX StorageClass On Host    ${host_sc}
    Create Guest StorageClass    ${MULTI_CLUSTER_ID}    ${guest_sc}    ${host_sc}
    Create PVC RWX    ${MULTI_CLUSTER_ID}    ${pvc_name}    1Gi    ${guest_sc}

RWX StatefulSet with 2 replicas is deployed
    [Documentation]    Create a StatefulSet with 2 replicas mounting the RWX PVC.
    ${pvc_name}=    Set Variable    pvc-rwx-${MULTI_CLUSTER_NAME}
    ${sts_name}=    Set Variable    rwx-sts-${MULTI_CLUSTER_NAME}
    Create StatefulSet    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${sts_name}    busybox:stable    ${pvc_name}    2

Worker pool with 1 node is added
    [Documentation]    Scale up the multi-node cluster by adding a worker pool.
    Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    1    ${MULTI_CONFIG_NAME}

Worker pool is removed
    [Documentation]    Scale down the multi-node cluster by removing the worker pool.
    Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    0    ${MULTI_CONFIG_NAME}

Multi node cluster is upgraded to next version
    [Documentation]    Trigger RKE2 upgrade to the next available patch version.
    Log    Upgrading from ${RKE2_VERSION} to ${NEXT_RKE2_VERSION}    console=yes
    Upgrade RKE2 Cluster    ${MULTI_CLUSTER_NAME}    ${NEXT_RKE2_VERSION}

New CSI workload is deployed
    [Arguments]    ${suffix}    ${cluster_id}=${MULTI_CLUSTER_ID}    ${cluster_name}=${MULTI_CLUSTER_NAME}
    [Documentation]    Create a new PVC and nginx deployment for post-operation verification.
    ${pvc_name}=    Set Variable    pvc-${suffix}-${cluster_name}
    ${deploy_name}=    Set Variable    csi-${suffix}-${cluster_name}
    Create PVC    ${cluster_id}    ${pvc_name}    1Gi
    Create Deployment    ${cluster_id}    ${DEFAULT_NAMESPACE}    ${deploy_name}    nginx:1.27    ${pvc_name}

All test workloads are removed from cluster
    [Documentation]    Delete all test deployments, PVCs, and LB services from the multi-node cluster.
    ${csi_deploy}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-dhcp
    ${lb_pool}=    Set Variable    lb-${MULTI_CLUSTER_NAME}-pool
    # Delete workloads
    Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Delete PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Delete LB Service    ${MULTI_CLUSTER_ID}    ${lb_dhcp}
    Delete LB Service    ${MULTI_CLUSTER_ID}    ${lb_pool}
    FOR    ${whoami}    IN    @{WHOAMI_DEPLOYMENTS}
        Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami}
        Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami}
    END

Single node RKE2 cluster is deleted
    [Documentation]    Delete the single-node RKE2 cluster and wait for removal.
    Log    Deleting: ${SINGLE_CLUSTER_NAME}    console=yes
    Delete RKE2 Cluster    ${SINGLE_CLUSTER_NAME}
    Wait For RKE2 Cluster Deleted    ${SINGLE_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

Single node custom RKE2 cluster is deleted
    [Documentation]    Delete the custom RKE2 cluster, its VMs, and wait for removal.
    Log    Deleting custom cluster: ${CUSTOM_CLUSTER_NAME}    console=yes
    Delete RKE2 Cluster    ${CUSTOM_CLUSTER_NAME}
    Wait For RKE2 Cluster Deleted    ${CUSTOM_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Run Keyword And Ignore Error    Delete Harvester VM    ${CUSTOM_CLUSTER_NAME}-vm-0
    Run Keyword And Ignore Error    Wait For Harvester VM Deleted    ${CUSTOM_CLUSTER_NAME}-vm-0    ${RANCHER_WAIT_TIMEOUT}

Single node import RKE2 cluster is created
    [Documentation]    Create a single-node import RKE2 cluster where RKE2 is deployed
    ...               via cloud-init on a Harvester VM and the cluster is imported
    ...               into Rancher. Store its ID.
    Log    Creating import cluster: ${IMPORT_CLUSTER_NAME}    console=yes
    ${cluster_id}=    Create Import RKE2 Cluster
    ...    ${IMPORT_CLUSTER_NAME}    1
    Set Suite Variable    ${IMPORT_CLUSTER_ID}    ${cluster_id}
    Set Suite Variable    ${IMPORT_CLUSTER_READY}    ${True}
    Log    Import cluster created: ${IMPORT_CLUSTER_NAME} (${cluster_id})    console=yes

CSI workload is deployed on single node import cluster
    [Documentation]    Deploy a CSI-backed workload (PVC + nginx deployment) on the
    ...               import cluster to exercise the Harvester CSI driver.
    ${pvc_name}=    Set Variable    pvc-${IMPORT_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${IMPORT_CLUSTER_NAME}
    Create PVC    ${IMPORT_CLUSTER_ID}    ${pvc_name}    1Gi
    Create Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    nginx:1.27    ${pvc_name}

Cloud provider workloads are deployed on single node import cluster
    [Arguments]    ${suffix}=${EMPTY}
    [Documentation]    Deploy a Whoami workload with DHCP and IP Pool LoadBalancer
    ...               services on the import cluster to exercise the Harvester cloud
    ...               provider.
    IF    '${suffix}' == '${EMPTY}'
        ${base}=    Set Variable    ${IMPORT_CLUSTER_NAME}
    ELSE
        ${base}=    Set Variable    ${suffix}-${IMPORT_CLUSTER_NAME}
    END
    # Whoami workload
    ${whoami_deploy}=    Set Variable    whoami-${base}
    Create Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    traefik/whoami:v1.11.0
    # LB DHCP
    ${lb_dhcp}=    Set Variable    lb-${base}-dhcp
    Create LB Service    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_dhcp}    ${whoami_deploy}    ipam=dhcp
    Wait For LB Service Ready    ${IMPORT_CLUSTER_ID}    ${lb_dhcp}
    # LB Pool
    ${lb_pool}=    Set Variable    lb-${base}-pool
    Create LB Service    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${lb_pool}    ${whoami_deploy}    ipam=pool
    Wait For LB Service Ready    ${IMPORT_CLUSTER_ID}    ${lb_pool}

Harvester CSI driver chart is installed on single node import cluster
    [Arguments]    ${version}=${CSI_CHART_VERSION}
    [Documentation]    Install the Harvester CSI Driver chart on the import cluster.
    ...               When version is empty the latest available version is used.
    Install Harvester CSI Driver Chart On Import Cluster    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}    ${version}
    Harvester CSI driver should be ready    ${IMPORT_CLUSTER_ID}

Harvester cloud provider chart is installed on single node import cluster
    [Arguments]    ${version}=${CP_CHART_VERSION}
    [Documentation]    Install the Harvester Cloud Provider chart on the import cluster.
    ...               When version is empty the latest available version is used.
    Install Harvester Cloud Provider Chart On Import Cluster    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}    ${version}
    Harvester cloud provider should be ready    ${IMPORT_CLUSTER_ID}

Multiple Harvester CSI driver chart versions are available
    [Documentation]    Ensure the rancher-charts repo offers at least two CSI driver
    ...               chart versions so an upgrade can be tested.
    ...               If CSI_CHART_VERSION is set, it is used as the target (latest)
    Ensure Harvester Chart Prerequisites On Import Cluster    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}
    ${versions}=    Get Chart Versions    rancher-charts    harvester-csi-driver    ${IMPORT_CLUSTER_ID}
    ${count}=    Get Length    ${versions}
    IF    '${CSI_CHART_VERSION}' != '${EMPTY}'
        ${idx}=    Get Index From List    ${versions}    ${CSI_CHART_VERSION}
        Should Not Be Equal As Integers    ${idx}    -1
        ...    CSI chart version ${CSI_CHART_VERSION} not found in available versions: ${versions}
        ${prev_idx}=    Evaluate    ${idx} + 1
        Skip If    ${prev_idx} >= ${count}
        ...    No older version available before ${CSI_CHART_VERSION}; cannot test upgrade
        ${latest}=    Set Variable    ${CSI_CHART_VERSION}
        ${previous}=    Get From List    ${versions}    ${prev_idx}
    ELSE
        Skip If    ${count} < 2
        ...    Only ${count} harvester-csi-driver chart version(s) available; need at least 2 to test upgrade
        ${latest}=    Get From List    ${versions}    0
        ${previous}=    Get From List    ${versions}    1
    END
    Set Suite Variable    ${CSI_LATEST_VERSION}    ${latest}
    Set Suite Variable    ${CSI_PREV_VERSION}    ${previous}
    Log    CSI chart upgrade path: ${previous} -> ${latest}    console=yes

Harvester CSI driver chart is upgraded to latest on import cluster
    [Documentation]    Upgrade the Harvester CSI Driver chart to the latest version
    ...               and verify the deployed chart version matches.
    ${csi_values}=    Evaluate    {"cloudConfig": {"hostPath": "", "secretName": "harvester-cloud-provider-config"}}
    Upgrade Chart
    ...    ${IMPORT_CLUSTER_ID}    rancher-charts    harvester-csi-driver
    ...    ${CSI_LATEST_VERSION}    harvester-csi-driver    kube-system    ${csi_values}
    Wait For Chart App Ready
    ...    ${IMPORT_CLUSTER_ID}    harvester-csi-driver    kube-system
    ...    expected_version=${CSI_LATEST_VERSION}
    Log    Upgraded harvester-csi-driver to ${CSI_LATEST_VERSION}    console=yes

CSI upgrade workload is restarted on import cluster
    [Documentation]    Scale the CSI workload down to 0 and back up to 1 to confirm
    ...               the upgraded CSI driver can re-attach the volume.
    ${csi_deploy}=    Set Variable    csi-${IMPORT_CLUSTER_NAME}
    Scale Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    0
    Wait For Deployment Scaled    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    0
    Scale Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}    1
    Wait For Deployment Ready    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Log    CSI workload restarted on import cluster    console=yes

Cleanup CSI upgrade test resources on import cluster
    [Documentation]    Delete CSI workloads and PVCs and uninstall the CSI driver
    ...               chart so the subsequent install test starts clean.
    Run Keyword And Ignore Error    Delete Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    csi-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Delete Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    csi-csiup-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Delete PVC    ${IMPORT_CLUSTER_ID}    pvc-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Delete PVC    ${IMPORT_CLUSTER_ID}    pvc-csiup-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Uninstall Chart    ${IMPORT_CLUSTER_ID}    harvester-csi-driver    kube-system
    Run Keyword And Ignore Error    Wait For Chart App Deleted    ${IMPORT_CLUSTER_ID}    harvester-csi-driver    kube-system

Multiple Harvester cloud provider chart versions are available
    [Documentation]    Ensure the rancher-charts repo offers at least two cloud provider
    ...               chart versions so an upgrade can be tested.
    ...               If CP_CHART_VERSION is set, it is used as the target (latest) version
    Ensure Harvester Chart Prerequisites On Import Cluster    ${IMPORT_CLUSTER_ID}    ${IMPORT_CLUSTER_NAME}
    ${versions}=    Get Chart Versions    rancher-charts    harvester-cloud-provider    ${IMPORT_CLUSTER_ID}
    ${count}=    Get Length    ${versions}
    IF    '${CP_CHART_VERSION}' != '${EMPTY}'
        ${idx}=    Get Index From List    ${versions}    ${CP_CHART_VERSION}
        Should Not Be Equal As Integers    ${idx}    -1
        ...    Cloud provider chart version ${CP_CHART_VERSION} not found in available versions: ${versions}
        ${prev_idx}=    Evaluate    ${idx} + 1
        Skip If    ${prev_idx} >= ${count}
        ...    No older version available before ${CP_CHART_VERSION}; cannot test upgrade
        ${latest}=    Set Variable    ${CP_CHART_VERSION}
        ${previous}=    Get From List    ${versions}    ${prev_idx}
    ELSE
        Skip If    ${count} < 2
        ...    Only ${count} harvester-cloud-provider chart version(s) available; need at least 2 to test upgrade
        ${latest}=    Get From List    ${versions}    0
        ${previous}=    Get From List    ${versions}    1
    END
    Set Suite Variable    ${CP_LATEST_VERSION}    ${latest}
    Set Suite Variable    ${CP_PREV_VERSION}    ${previous}
    Log    Cloud provider chart upgrade path: ${previous} -> ${latest}    console=yes

Harvester cloud provider chart is upgraded to latest on import cluster
    [Documentation]    Upgrade the Harvester Cloud Provider chart to the latest version
    ...               and verify the deployed chart version matches.
    ${cp_values}=    Evaluate    {"cloudConfigPath": "/var/lib/rancher/rke2/etc/config-files/cloud-provider-config", "global": {"cattle": {"clusterName": "${IMPORT_CLUSTER_ID}"}}}
    Upgrade Chart
    ...    ${IMPORT_CLUSTER_ID}    rancher-charts    harvester-cloud-provider
    ...    ${CP_LATEST_VERSION}    harvester-cloud-provider    kube-system    ${cp_values}
    Wait For Chart App Ready
    ...    ${IMPORT_CLUSTER_ID}    harvester-cloud-provider    kube-system
    ...    expected_version=${CP_LATEST_VERSION}
    Log    Upgraded harvester-cloud-provider to ${CP_LATEST_VERSION}    console=yes

Cloud provider upgrade workload is restarted on import cluster
    [Documentation]    Scale the Whoami workload down to 0 and back up to 1 to confirm
    ...               the upgraded cloud provider keeps serving the LoadBalancer.
    ${whoami_deploy}=    Set Variable    whoami-${IMPORT_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${IMPORT_CLUSTER_NAME}-dhcp
    Scale Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    0
    Wait For Deployment Scaled    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    0
    Scale Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}    1
    Wait For Deployment Ready    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Verify LB Via Cluster    ${IMPORT_CLUSTER_ID}    ${lb_dhcp}    Hostname:
    Log    Cloud provider workload restarted on import cluster    console=yes

Cleanup cloud provider upgrade test resources on import cluster
    [Documentation]    Delete cloud provider workloads and LoadBalancers and uninstall
    ...               the cloud provider chart so the subsequent install test starts clean.
    Run Keyword And Ignore Error    Delete LB Service    ${IMPORT_CLUSTER_ID}    lb-${IMPORT_CLUSTER_NAME}-dhcp
    Run Keyword And Ignore Error    Delete LB Service    ${IMPORT_CLUSTER_ID}    lb-${IMPORT_CLUSTER_NAME}-pool
    Run Keyword And Ignore Error    Delete LB Service    ${IMPORT_CLUSTER_ID}    lb-cpup2-${IMPORT_CLUSTER_NAME}-dhcp
    Run Keyword And Ignore Error    Delete LB Service    ${IMPORT_CLUSTER_ID}    lb-cpup2-${IMPORT_CLUSTER_NAME}-pool
    Run Keyword And Ignore Error    Delete Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    whoami-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Delete Deployment    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    whoami-cpup2-${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Uninstall Chart    ${IMPORT_CLUSTER_ID}    harvester-cloud-provider    kube-system
    Run Keyword And Ignore Error    Wait For Chart App Deleted    ${IMPORT_CLUSTER_ID}    harvester-cloud-provider    kube-system

Multi node RKE2 cluster is deleted
    [Documentation]    Delete the multi-node RKE2 cluster and wait for removal.
    Log    Deleting: ${MULTI_CLUSTER_NAME}    console=yes
    Delete RKE2 Cluster    ${MULTI_CLUSTER_NAME}
    Wait For RKE2 Cluster Deleted    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

# ============================================================
# BDD Keywords - Then (Verifications)
# ============================================================
Harvester deployments should be ready
    [Arguments]    ${cluster_id}
    [Documentation]    Verify harvester-cloud-provider and CSI driver are active.
    Wait For Deployment Ready    ${cluster_id}    kube-system    harvester-csi-driver-controllers
    Wait For Deployment Ready    ${cluster_id}    kube-system    harvester-cloud-provider

Harvester CSI driver should be ready
    [Arguments]    ${cluster_id}
    Wait For Deployment Ready    ${cluster_id}    kube-system    harvester-csi-driver-controllers

Harvester cloud provider should be ready
    [Arguments]    ${cluster_id}
    Wait For Deployment Ready    ${cluster_id}    kube-system    harvester-cloud-provider

Import cluster should be ready and running
    [Documentation]    Verify the imported cluster is active and running in Rancher.
    Should Not Be Empty    ${IMPORT_CLUSTER_ID}    Import cluster ID not set
    Wait For Import Cluster Ready    ${IMPORT_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Log    Import cluster ${IMPORT_CLUSTER_NAME} (${IMPORT_CLUSTER_ID}) is ready and running    console=yes

Basic workloads should be active on single node cluster
    [Documentation]    Verify CSI, Whoami, and both LB services are functional on the single-node cluster.
    ${pvc_name}=    Set Variable    pvc-${SINGLE_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${SINGLE_CLUSTER_NAME}
    ${whoami_deploy}=    Set Variable    whoami-${SINGLE_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-dhcp
    ${lb_pool}=    Set Variable    lb-${SINGLE_CLUSTER_NAME}-pool
    Wait For PVC Bound    ${SINGLE_CLUSTER_ID}    ${pvc_name}
    Wait For Deployment Ready    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Wait For Deployment Ready    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Verify LB Via Cluster    ${SINGLE_CLUSTER_ID}    ${lb_dhcp}    Hostname:
    Verify LB Via Cluster    ${SINGLE_CLUSTER_ID}    ${lb_pool}    Hostname:
    Log    All basic workloads verified on single-node cluster    console=yes

Basic workloads should be active on single node custom cluster
    [Documentation]    Verify CSI, Whoami, and both LB services are functional on the custom cluster.
    ${pvc_name}=    Set Variable    pvc-${CUSTOM_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${CUSTOM_CLUSTER_NAME}
    ${whoami_deploy}=    Set Variable    whoami-${CUSTOM_CLUSTER_NAME}
    ${lb_dhcp}=    Set Variable    lb-${CUSTOM_CLUSTER_NAME}-dhcp
    ${lb_pool}=    Set Variable    lb-${CUSTOM_CLUSTER_NAME}-pool
    Wait For PVC Bound    ${CUSTOM_CLUSTER_ID}    ${pvc_name}
    Wait For Deployment Ready    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Wait For Deployment Ready    ${CUSTOM_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Verify LB Via Cluster    ${CUSTOM_CLUSTER_ID}    ${lb_dhcp}    Hostname:
    Verify LB Via Cluster    ${CUSTOM_CLUSTER_ID}    ${lb_pool}    Hostname:
    Log    All basic workloads verified on custom cluster    console=yes

CSI workload should be active on single node import cluster
    [Documentation]    Verify the CSI PVC is bound and the CSI-backed deployment is
    ...               running on the import cluster.
    ${pvc_name}=    Set Variable    pvc-${IMPORT_CLUSTER_NAME}
    ${csi_deploy}=    Set Variable    csi-${IMPORT_CLUSTER_NAME}
    Wait For PVC Bound    ${IMPORT_CLUSTER_ID}    ${pvc_name}
    Wait For Deployment Ready    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    Log    CSI workload verified on import cluster    console=yes

Cloud provider workloads should be active on single node import cluster
    [Arguments]    ${suffix}=${EMPTY}
    [Documentation]    Verify the Whoami deployment and both LB services (DHCP and IP
    ...               Pool) are functional on the import cluster. An optional suffix
    ...               selects the matching workload set.
    IF    '${suffix}' == '${EMPTY}'
        ${base}=    Set Variable    ${IMPORT_CLUSTER_NAME}
    ELSE
        ${base}=    Set Variable    ${suffix}-${IMPORT_CLUSTER_NAME}
    END
    ${whoami_deploy}=    Set Variable    whoami-${base}
    ${lb_dhcp}=    Set Variable    lb-${base}-dhcp
    ${lb_pool}=    Set Variable    lb-${base}-pool
    Wait For Deployment Ready    ${IMPORT_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami_deploy}
    Verify LB Via Cluster    ${IMPORT_CLUSTER_ID}    ${lb_dhcp}    Hostname:
    Verify LB Via Cluster    ${IMPORT_CLUSTER_ID}    ${lb_pool}    Hostname:
    Log    Cloud provider workloads verified on import cluster    console=yes

CSI deployment and PVC should be active
    [Documentation]    Verify the CSI PVC is bound and deployment is running.
    ${pvc_name}=    Set Variable    pvc-${MULTI_CLUSTER_NAME}
    ${deploy_name}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    Wait For PVC Bound    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Log    CSI deployment ready: ${deploy_name}    console=yes

Whoami deployment should be active
    [Arguments]    ${suffix}
    [Documentation]    Verify the Whoami deployment is running.
    ...               Args:
    ...                   suffix: Suffix matching the Whoami deployment
    ${deploy_name}=    Set Variable    whoami-${suffix}-${MULTI_CLUSTER_NAME}
    Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Log    Whoami deployment ready: ${deploy_name}    console=yes

DHCP load balancer should be serving traffic
    [Documentation]    Verify the DHCP load balancer responds via Rancher proxy.
    Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_DHCP_NAME}    Hostname:

Pool load balancer should be serving traffic
    [Documentation]    Verify the pool load balancer responds via Rancher proxy.
    Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_POOL_NAME}    Hostname:

RWX StatefulSet should be ready
    [Documentation]    Verify the RWX StatefulSet has all replicas ready and PVC is bound.
    ${pvc_name}=    Set Variable    pvc-rwx-${MULTI_CLUSTER_NAME}
    ${sts_name}=    Set Variable    rwx-sts-${MULTI_CLUSTER_NAME}
    Wait For PVC Bound    ${MULTI_CLUSTER_ID}    ${pvc_name}
    Wait For StatefulSet Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${sts_name}
    Log    RWX StatefulSet ready: ${sts_name}    console=yes

RWX shared data should be accessible across pods
    [Documentation]    Write data from one pod and read it from another pod to verify
    ...               ReadWriteMany volume sharing works correctly.
    ${sts_name}=    Set Variable    rwx-sts-${MULTI_CLUSTER_NAME}
    ${label}=    Set Variable    name=${sts_name}
    ${pods}=    Get Pods By Label    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${label}
    ${pod_count}=    Get Length    ${pods}
    Should Be True    ${pod_count} >= 2    Expected at least 2 pods, got ${pod_count}
    ${pod0_name}=    Set Variable    ${pods}[0][metadata][name]
    ${pod1_name}=    Set Variable    ${pods}[1][metadata][name]
    # Write from first pod
    ${write_cmd}=    Create List    sh    -c    echo rwx-test-data > /data/rwx-verify.txt
    Exec Command In Pod    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${pod0_name}    @{write_cmd}
    # Read from second pod
    ${read_cmd}=    Create List    cat    /data/rwx-verify.txt
    ${output}=    Exec Command In Pod    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${pod1_name}    @{read_cmd}
    Should Contain    ${output}    rwx-test-data    RWX data not found in second pod
    Log    RWX volume sharing verified: data written by ${pod0_name}, read by ${pod1_name}    console=yes

RWX StatefulSet should be ready on single node cluster
    [Documentation]    Verify the RWX StatefulSet has all replicas ready and PVC is bound
    ...               on the single-node cluster.
    ${pvc_name}=    Set Variable    pvc-rwx-${SINGLE_CLUSTER_NAME}
    ${sts_name}=    Set Variable    rwx-sts-${SINGLE_CLUSTER_NAME}
    Wait For PVC Bound    ${SINGLE_CLUSTER_ID}    ${pvc_name}
    Wait For StatefulSet Ready    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${sts_name}
    Log    RWX StatefulSet ready on single cluster: ${sts_name}    console=yes

RWX shared data should be accessible across pods on single node cluster
    [Documentation]    Write data from one pod and read it from another pod to verify
    ...               ReadWriteMany volume sharing works on the single-node cluster.
    ${sts_name}=    Set Variable    rwx-sts-${SINGLE_CLUSTER_NAME}
    ${label}=    Set Variable    name=${sts_name}
    ${pods}=    Get Pods By Label    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${label}
    ${pod_count}=    Get Length    ${pods}
    Should Be True    ${pod_count} >= 2    Expected at least 2 pods, got ${pod_count}
    ${pod0_name}=    Set Variable    ${pods}[0][metadata][name]
    ${pod1_name}=    Set Variable    ${pods}[1][metadata][name]
    # Write from first pod
    ${write_cmd}=    Create List    sh    -c    echo rwx-test-data > /data/rwx-verify.txt
    Exec Command In Pod    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${pod0_name}    @{write_cmd}
    # Read from second pod
    ${read_cmd}=    Create List    cat    /data/rwx-verify.txt
    ${output}=    Exec Command In Pod    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${pod1_name}    @{read_cmd}
    Should Contain    ${output}    rwx-test-data    RWX data not found in second pod
    Log    RWX volume sharing verified: data written by ${pod0_name}, read by ${pod1_name}    console=yes

Cleanup RWX test resources on single node cluster
    [Documentation]    Clean up RWX resources from the single-node cluster and disable
    ...               storage network (stopping and restarting VMs as required).
    Log    Cleaning up RWX test resources on single cluster    console=yes

    # Delete RWX guest cluster resources
    ${rwx_sts}=    Set Variable    rwx-sts-${SINGLE_CLUSTER_NAME}
    ${rwx_pvc}=    Set Variable    pvc-rwx-${SINGLE_CLUSTER_NAME}
    ${rwx_guest_sc}=    Set Variable    rwx-guest-sc-${SINGLE_CLUSTER_NAME}
    Run Keyword And Ignore Error    Delete StatefulSet    ${SINGLE_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${rwx_sts}
    Run Keyword And Ignore Error    Delete PVC    ${SINGLE_CLUSTER_ID}    ${rwx_pvc}
    Run Keyword And Ignore Error    Delete Guest StorageClass    ${SINGLE_CLUSTER_ID}    ${rwx_guest_sc}
    Run Keyword And Ignore Error    Delete RWX StorageClass On Host    ${RWX_HOST_STORAGE_CLASS}

    # Disable storage network (stops/restarts all VMs)
    Run Keyword And Ignore Error    Disable storage network for RWX

    Log    RWX cleanup completed on single cluster    console=yes

Single node cluster should be ready
    [Documentation]    Wait for the single-node RKE2 cluster and Harvester deployments
    ...               to recover after a disruptive operation (e.g. storage network change).
    Wait For RKE2 Cluster Ready    ${SINGLE_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Wait For Harvester Deployments Ready    ${SINGLE_CLUSTER_ID}

Multi node cluster should be ready
    [Documentation]    Wait for the multi-node cluster to become active and ready.
    Wait For RKE2 Cluster Ready    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

All existing workloads should be active
    [Documentation]    Verify all system and application workloads are running.
    Wait For Harvester Deployments Ready    ${MULTI_CLUSTER_ID}
    ${csi_deploy}=    Set Variable    csi-${MULTI_CLUSTER_NAME}
    Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${csi_deploy}
    FOR    ${whoami}    IN    @{WHOAMI_DEPLOYMENTS}
        Wait For Deployment Ready    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${whoami}
    END
    Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_DHCP_NAME}    Hostname:
    Verify LB Via Cluster    ${MULTI_CLUSTER_ID}    ${LB_POOL_NAME}    Hostname:
    Log    All existing workloads verified active    console=yes

New CSI workload should be active
    [Arguments]    ${suffix}    ${cluster_id}=${MULTI_CLUSTER_ID}    ${cluster_name}=${MULTI_CLUSTER_NAME}
    [Documentation]    Verify the new CSI PVC and deployment are active.
    ${pvc_name}=    Set Variable    pvc-${suffix}-${cluster_name}
    ${deploy_name}=    Set Variable    csi-${suffix}-${cluster_name}
    Wait For PVC Bound    ${cluster_id}    ${pvc_name}
    Wait For Deployment Ready    ${cluster_id}    ${DEFAULT_NAMESPACE}    ${deploy_name}
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
    Run Keyword And Ignore Error    Delete Deployment    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Run Keyword And Ignore Error    Wait For Deployment Deleted    ${MULTI_CLUSTER_ID}    ${DEFAULT_NAMESPACE}    ${deploy_name}
    Run Keyword And Ignore Error    Delete PVC    ${MULTI_CLUSTER_ID}    ${pvc_name}

Cleanup upgrade test resources
    [Documentation]    Clean up resources created during the upgrade test.
    Run Keyword And Ignore Error    Cleanup temporary workloads    upgrade
    Run Keyword And Ignore Error    Scale RKE2 Cluster    ${MULTI_CLUSTER_NAME}    0    ${MULTI_CONFIG_NAME}
    Run Keyword And Ignore Error    Wait For RKE2 Cluster Ready    ${MULTI_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}

Cleanup custom cluster test resources
    [Documentation]    Clean up all resources created by the custom cluster test.
    ...               Deletes the RKE2 cluster, waits for deletion, then removes
    ...               the Harvester VM that was created for the node.
    Run Keyword And Ignore Error    Delete RKE2 Cluster    ${CUSTOM_CLUSTER_NAME}
    Run Keyword And Ignore Error    Wait For RKE2 Cluster Deleted    ${CUSTOM_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Run Keyword And Ignore Error    Delete Harvester VM    ${CUSTOM_CLUSTER_NAME}-vm-0
    Run Keyword And Ignore Error    Wait For Harvester VM Deleted    ${CUSTOM_CLUSTER_NAME}-vm-0    ${RANCHER_WAIT_TIMEOUT}

Cleanup import cluster test resources
    [Documentation]    Clean up all resources created by the import cluster test.
    ...               Deletes the provisioning cluster, waits for deletion, then
    ...               removes the Harvester VM that was created for the node.
    Run Keyword And Ignore Error    Delete RKE2 Cluster    ${IMPORT_CLUSTER_NAME}
    Run Keyword And Ignore Error    Wait For RKE2 Cluster Deleted    ${IMPORT_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Run Keyword And Ignore Error    Delete Harvester VM    ${IMPORT_CLUSTER_NAME}-vm-0
    Run Keyword And Ignore Error    Wait For Harvester VM Deleted    ${IMPORT_CLUSTER_NAME}-vm-0    ${RANCHER_WAIT_TIMEOUT}

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
    ${secret}=    Create Cloud Provider Secret    ${cluster_name}    ${CP_KUBECONFIG}    ${cluster_name}
    ${cloud_provider_config_id}=    Set Variable    ${secret}[metadata][namespace]:${secret}[metadata][name]

    # Harvester config (per-cluster for scale ops)
    Create Harvester Config
    ...    ${config_name}
    ...    image_id=${DEFAULT_NAMESPACE}/${IMAGE_NAME}
    ...    network_id=${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
    ...    ssh_user=ubuntu

    # Create RKE2 cluster
    Create RKE2 Cluster
    ...    ${cluster_name}
    ...    ${cloud_provider_config_id}
    ...    ${cluster_name}-
    ...    ${config_name}
    ...    ${rke2_version}
    ...    ${CLOUD_CREDENTIAL_ID}
    ...    ${machine_count}
    ...    ${ingress}

    # Wait for ready
    ${cluster}=    Wait For RKE2 Cluster Ready    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    ${rke2_installed}=    Set Variable    ${cluster}[spec][kubernetesVersion]
    Log    Cluster ready: ${cluster_name} (ID: ${cluster_id}) RKE2 version: ${rke2_installed}    console=yes

    RETURN    ${cluster_id}

# ============================================================
# Shared custom cluster creation keyword
# ============================================================
Create Custom RKE2 Cluster With Full Setup
    [Arguments]    ${cluster_name}    ${rke2_version}    ${machine_count}
    ...            ${ingress}=${INGRESS_CONTROLLER}
    [Documentation]    Create a custom RKE2 cluster with Harvester cloud provider.
    ...               VMs are created on Harvester with cloud-init that runs the
    ...               registration command to join the cluster.
    ...               Uses shared cloud credential from suite setup.
    ...               Returns cluster ID.

    # Cloud provider secret (per-cluster)
    ${secret}=    Create Cloud Provider Secret    ${cluster_name}    ${CP_KUBECONFIG}    ${cluster_name}
    ${cloud_provider_config_id}=    Set Variable    ${secret}[metadata][namespace]:${secret}[metadata][name]

    # Create custom RKE2 cluster (no machinePools)
    Create Custom RKE2 Cluster
    ...    ${cluster_name}
    ...    ${cloud_provider_config_id}
    ...    ${rke2_version}
    ...    ${CLOUD_CREDENTIAL_ID}
    ...    ${ingress}

    # Wait for cluster to get its management ID
    ${cluster}=    Wait For Cluster ID    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${mgmt_cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Log    Custom cluster management ID: ${mgmt_cluster_id}    console=yes

    # Patch chartValues with the real management cluster ID so the cloud
    # provider can correctly identify VMs belonging to this cluster.
    # At creation time only the provisioning name is known; the management
    # ID (c-m-xxxxx) is assigned by Rancher afterwards.
    Update Cluster Chart Name    ${cluster_name}    ${mgmt_cluster_id}

    # Get the registration command
    ${reg_command}=    Get Cluster Registration Command    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    Log    Got registration command for ${cluster_name}    console=yes

    # Build cloud-init userData with the registration command
    # The reg_command from Rancher contains single-quoted values like
    # --label 'cattle.io/os=linux', so we must use double quotes for
    # the outer shell command to avoid broken YAML.
    ${user_data}=    Catenate    SEPARATOR=\n
    ...    \#cloud-config
    ...    password: password
    ...    chpasswd:
    ...    ${SPACE}${SPACE}expire: false
    ...    ssh_pwauth: true
    ...    package_update: true
    ...    packages:
    ...    ${SPACE}${SPACE}- qemu-guest-agent
    ...    ${SPACE}${SPACE}- curl
    ...    runcmd:
    ...    ${SPACE}${SPACE}- [systemctl, enable, --now, qemu-guest-agent.service]
    ...    ${SPACE}${SPACE}- [/bin/sh, -c, "${reg_command} --etcd --controlplane --worker"]

    # Create VMs on Harvester with the registration command
    # With a single bridge interface on the VLAN, DHCP works automatically
    # on the first NIC — no explicit network_data needed.
    FOR    ${i}    IN RANGE    ${machine_count}
        ${vm_name}=    Set Variable    ${cluster_name}-vm-${i}
        Create Harvester VM
        ...    ${vm_name}
        ...    ${DEFAULT_NAMESPACE}/${IMAGE_NAME}
        ...    ${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
        ...    cpus=4
        ...    memory=8
        ...    disk_size=40
        ...    ssh_user=ubuntu
        ...    user_data=${user_data}
        ...    guest_cluster_id=${mgmt_cluster_id}
        Wait For Harvester VM Ready    ${vm_name}    ${WAIT_TIMEOUT}
    END

    # Wait for RKE2 cluster to become ready
    ${cluster}=    Wait For RKE2 Cluster Ready    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Log    Custom cluster ready: ${cluster_name} (ID: ${cluster_id})    console=yes

    # Fix cloud provider clusterName on the guest cluster.
    # Rancher deploys the chart with the provisioning name, but the
    # cloud provider needs the management cluster ID (c-m-xxxxx) to
    # match VMs via the harvesterhci.io/owned-by label.
    Fix Cloud Provider Cluster Name    ${cluster_id}

    RETURN    ${cluster_id}

# ============================================================
# Shared import cluster creation keyword
# ============================================================
Ensure Harvester Chart Prerequisites On Import Cluster
    [Arguments]    ${cluster_id}    ${cluster_name}    ${chart_repo_branch}=${CHART_REPO_BRANCH}
    [Documentation]    Create the shared prerequisites for installing Harvester charts:
    ...               the rancher-charts ClusterRepo and cloud-provider-config secret.
    IF    ${IMPORT_CHART_PREREQS_DONE}
        Log    Harvester chart prerequisites already created on ${cluster_name}    console=yes
        RETURN
    END
    Log    Creating Harvester chart prerequisites on import cluster ${cluster_name}    console=yes

    # Create rancher-charts ClusterRepo on the guest cluster
    Create Cluster Repo
    ...    ${cluster_id}    rancher-charts    ${CHART_REPO_URL}    ${chart_repo_branch}
    Wait For Cluster Repo Ready    ${cluster_id}    rancher-charts
    ...    expected_git_branch=${chart_repo_branch}
    Log    ClusterRepo rancher-charts (branch=${chart_repo_branch}) is ready    console=yes

    # Create cloud-provider-config secret on the guest cluster
    Create Cloud Config Secret
    ...    ${cluster_id}    harvester-cloud-provider-config    kube-system    ${CP_KUBECONFIG}

    Set Suite Variable    ${IMPORT_CHART_PREREQS_DONE}    ${True}

Install Harvester CSI Driver Chart On Import Cluster
    [Arguments]    ${cluster_id}    ${cluster_name}    ${version}=${EMPTY}
    [Documentation]    Install the Harvester CSI Driver chart from Rancher Apps on an
    ...               imported cluster. Uses the cloud-config secret (instead of a
    ...               hostPath) and waits for the chart app to be deployed.
    Ensure Harvester Chart Prerequisites On Import Cluster    ${cluster_id}    ${cluster_name}

    # Resolve CSI driver chart version (latest when not specified)
    IF    '${version}' == '${EMPTY}'
        ${csi_versions}=    Get Chart Versions    rancher-charts    harvester-csi-driver    ${cluster_id}
        ${version}=    Get From List    ${csi_versions}    0
    END
    Log    harvester-csi-driver chart version: ${version}    console=yes

    # Install Harvester CSI Driver — use secret instead of hostPath
    ${csi_values}=    Evaluate    {"cloudConfig": {"hostPath": "", "secretName": "harvester-cloud-provider-config"}}
    Install Chart
    ...    ${cluster_id}    rancher-charts    harvester-csi-driver
    ...    ${version}    harvester-csi-driver    kube-system    ${csi_values}
    Wait For Chart App Ready    ${cluster_id}    harvester-csi-driver    kube-system
    Log    Harvester CSI Driver chart installed on import cluster    console=yes

Install Harvester Cloud Provider Chart On Import Cluster
    [Arguments]    ${cluster_id}    ${cluster_name}    ${version}=${EMPTY}
    [Documentation]    Install the Harvester Cloud Provider chart from Rancher Apps on
    ...               an imported cluster. Writes the cloud-config to the node hostPath
    ...               required by the chart and waits for the chart app to be deployed.
    Ensure Harvester Chart Prerequisites On Import Cluster    ${cluster_id}    ${cluster_name}

    # The cloud provider chart mounts the cloud-config file as a hostPath —
    # the file must exist on the node before the pod starts.
    Write Cloud Config To Nodes
    ...    ${cluster_id}    harvester-cloud-provider-config    kube-system

    # Resolve cloud provider chart version (latest when not specified)
    IF    '${version}' == '${EMPTY}'
        ${cp_versions}=    Get Chart Versions    rancher-charts    harvester-cloud-provider    ${cluster_id}
        ${version}=    Get From List    ${cp_versions}    0
    END
    Log    harvester-cloud-provider chart version: ${version}    console=yes

    # Install Harvester Cloud Provider
    ${cp_values}=    Evaluate    {"cloudConfigPath": "/var/lib/rancher/rke2/etc/config-files/cloud-provider-config", "global": {"cattle": {"clusterName": "${cluster_id}"}}}
    Install Chart
    ...    ${cluster_id}    rancher-charts    harvester-cloud-provider
    ...    ${version}    harvester-cloud-provider    kube-system    ${cp_values}
    Wait For Chart App Ready    ${cluster_id}    harvester-cloud-provider    kube-system
    Log    Harvester Cloud Provider chart installed on import cluster    console=yes

Write Cloud Config To Nodes
    [Arguments]    ${cluster_id}    ${secret_name}    ${namespace}
    [Documentation]    Deploy a temporary privileged DaemonSet on the guest cluster
    ...               that copies the cloud-provider-config secret to the node hostPath
    ...               required by the harvester-cloud-provider chart.
    ...               The DaemonSet is deleted once all nodes have been configured.
    Log    Writing cloud config to nodes on cluster ${cluster_id}    console=yes
    ${result}=    rancher_keywords.write_cloud_config_to_nodes
    ...    ${cluster_id}    ${secret_name}    ${namespace}
    RETURN    ${result}

Create Import RKE2 Cluster
    [Arguments]    ${cluster_name}    ${machine_count}    ${rke2_version}=${RKE2_VERSION}
    [Documentation]    Create a minimal import cluster in Rancher, deploy RKE2
    ...               on Harvester VMs via cloud-init, and import the cluster
    ...               using the Rancher registration manifest.
    ...               Returns management cluster ID.

    # Create a minimal provisioning cluster in Rancher (import mode)
    Create Import Cluster    ${cluster_name}

    # Wait for the cluster to get its management ID
    ${cluster}=    Wait For Cluster ID    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${mgmt_cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Log    Import cluster management ID: ${mgmt_cluster_id}    console=yes

    # Get the manifest URL for importing
    ${manifest_url}=    Get Cluster Registration URL
    ...    ${mgmt_cluster_id}    ${RANCHER_ENDPOINT}    ${RANCHER_WAIT_TIMEOUT}
    Log    Got manifest URL for ${cluster_name}    console=yes

    # Build cloud-init: install RKE2, start it, wait for ready, apply import manifest
    ${import_cmd}=    Set Variable    while [ ! -f /etc/rancher/rke2/rke2.yaml ]; do sleep 10; done && export KUBECONFIG=/etc/rancher/rke2/rke2.yaml && export PATH=$PATH:/var/lib/rancher/rke2/bin && while ! kubectl get nodes 2>/dev/null | grep -q Ready; do sleep 10; done && curl --insecure -sfL ${manifest_url} | kubectl apply -f -
    
    ${is_exact}=    Evaluate    '+' in '${rke2_version}'
    IF    ${is_exact}
        ${rke2_env}=    Set Variable    INSTALL_RKE2_VERSION=${rke2_version} INSTALL_RKE2_TYPE=server
        Log    RKE2 install: exact version ${rke2_version}    console=yes
    ELSE
        ${rke2_env}=    Set Variable    INSTALL_RKE2_CHANNEL=${rke2_version} INSTALL_RKE2_TYPE=server
        Log    RKE2 install: channel ${rke2_version} (latest patch will be resolved at install time)    console=yes
    END
    ${user_data}=    Catenate    SEPARATOR=\n
    ...    \#cloud-config
    ...    password: password
    ...    chpasswd:
    ...    ${SPACE}${SPACE}expire: false
    ...    ssh_pwauth: true
    ...    package_update: true
    ...    packages:
    ...    ${SPACE}${SPACE}- qemu-guest-agent
    ...    ${SPACE}${SPACE}- curl
    ...    runcmd:
    ...    ${SPACE}${SPACE}- [systemctl, enable, --now, qemu-guest-agent.service]
    ...    ${SPACE}${SPACE}- [/bin/sh, -c, 'curl -sfL https://get.rke2.io | ${rke2_env} sh -']
    ...    ${SPACE}${SPACE}- [/bin/sh, -c, 'mkdir -p /etc/rancher/rke2 && echo "disable-cloud-controller: true" > /etc/rancher/rke2/config.yaml']
    ...    ${SPACE}${SPACE}- [systemctl, enable, rke2-server.service]
    ...    ${SPACE}${SPACE}- [systemctl, start, rke2-server.service]
    ...    ${SPACE}${SPACE}- [/bin/sh, -c, '${import_cmd}']

    # Create VMs on Harvester with the cloud-init
    FOR    ${i}    IN RANGE    ${machine_count}
        ${vm_name}=    Set Variable    ${cluster_name}-vm-${i}
        Create Harvester VM
        ...    ${vm_name}
        ...    ${DEFAULT_NAMESPACE}/${IMAGE_NAME}
        ...    ${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
        ...    cpus=4
        ...    memory=8
        ...    disk_size=40
        ...    ssh_user=ubuntu
        ...    user_data=${user_data}
        ...    guest_cluster_id=${mgmt_cluster_id}
        Wait For Harvester VM Ready    ${vm_name}    ${WAIT_TIMEOUT}
    END

    # Wait for the imported cluster to become active in Rancher
    ${cluster}=    Wait For Import Cluster Ready    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Log    Import cluster ready: ${cluster_name} (ID: ${cluster_id})    console=yes

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
    # Harvester enforces a 12-character max on ClusterNetwork and VlanConfig names.
    ${ts_short}=    Evaluate    '${timestamp}'[-7:]
    Set Suite Variable    ${CLUSTER_NETWORK_NAME}    cnet-${ts_short}
    Set Suite Variable    ${VLAN_CONFIG_NAME}    vcfg-${ts_short}
    Set Suite Variable    ${IP_POOL_NAME}    ippool-vlan${VLAN_ID}
    Set Suite Variable    ${IMAGE_NAME}    ubuntu-${timestamp}

    # Derive cluster and config names from RKE2_VERSION
    ${version_suffix}=    Replace String    ${RKE2_VERSION}    +    -
    ${version_suffix}=    Replace String    ${version_suffix}    .    -
    Set Suite Variable    ${SINGLE_CLUSTER_NAME}    ${RKE2_CLUSTER_NAME}-${version_suffix}-single
    Set Suite Variable    ${MULTI_CLUSTER_NAME}     ${RKE2_CLUSTER_NAME}-${version_suffix}-multi
    Set Suite Variable    ${SINGLE_CONFIG_NAME}     ${RKE2_CLUSTER_NAME}-${version_suffix}-single-config
    Set Suite Variable    ${MULTI_CONFIG_NAME}      ${RKE2_CLUSTER_NAME}-${version_suffix}-multi-config
    Set Suite Variable    ${CUSTOM_CLUSTER_NAME}    ${RKE2_CLUSTER_NAME}-${version_suffix}-custom
    Set Suite Variable    ${IMPORT_CLUSTER_NAME}    ${RKE2_CLUSTER_NAME}-${version_suffix}-import

    # Cluster tracking
    Set Suite Variable    ${HARVESTER_CLUSTER_ID}    ${EMPTY}
    Set Suite Variable    ${CLOUD_CREDENTIAL_ID}    ${EMPTY}
    Set Suite Variable    ${SINGLE_CLUSTER_ID}      ${EMPTY}
    Set Suite Variable    ${MULTI_CLUSTER_ID}       ${EMPTY}
    Set Suite Variable    ${CUSTOM_CLUSTER_ID}      ${EMPTY}
    Set Suite Variable    ${IMPORT_CLUSTER_ID}      ${EMPTY}
    Set Suite Variable    ${IMPORT_CLUSTER_READY}        ${False}
    Set Suite Variable    ${IMPORT_CHART_PREREQS_DONE}    ${False}
    Set Suite Variable    ${LB_DHCP_NAME}           ${EMPTY}
    Set Suite Variable    ${LB_POOL_NAME}           ${EMPTY}
    @{whoami_list}=    Create List
    Set Suite Variable    @{WHOAMI_DEPLOYMENTS}     @{whoami_list}
    Set Suite Variable    ${NEXT_RKE2_VERSION}      ${EMPTY}

    # Resolve RKE2 version (prefix like v1.34 -> full version like v1.34.5+rke2r1)
    # Apply custom KDM first so the version list reflects the KDM data.json content
    Configure KDM If Custom
    ${is_full_version}=    Evaluate    '+' in '${RKE2_VERSION}'
    IF    not ${is_full_version}
        ${versions}=    Resolve RKE2 Versions
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
    ${cluster}=    Get Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}
    Should Not Be Empty    ${cluster}    Harvester cluster not found in Rancher
    Log    Harvester integration verified    console=yes

    # Generate shared kubeconfigs and cloud credential (used by all clusters)
    ${cp_kubeconfig}=    Generate Cloud Provider Kubeconfig
    ...    ${HARVESTER_CLUSTER_ID}    ${HARVESTER_CLUSTER_NAME}
    Set Suite Variable    ${CP_KUBECONFIG}    ${cp_kubeconfig}

    ${kubeconfig}=    Generate Kubeconfig    ${HARVESTER_CLUSTER_ID}    ${HARVESTER_CLUSTER_NAME}
    ${credential}=    Create Cloud Credential
    ...    ${RKE2_CLUSTER_NAME}
    ...    ${kubeconfig}
    ...    ${HARVESTER_CLUSTER_ID}
    Set Suite Variable    ${CLOUD_CREDENTIAL_ID}    ${credential}[id]

    # Create shared resources
    Create Cluster Network    ${CLUSTER_NETWORK_NAME}
    Create VLAN Config    ${VLAN_CONFIG_NAME}    ${CLUSTER_NETWORK_NAME}    ${VLAN_NIC}
    Wait For Cluster Network Ready    ${CLUSTER_NETWORK_NAME}
    Create VLAN Network    ${VLAN_NETWORK_NAME}    ${VLAN_ID}    ${CLUSTER_NETWORK_NAME}
    Create IP Pool
    ...    ${IP_POOL_NAME}
    ...    ${IP_POOL_SUBNET}
    ...    ${IP_POOL_START}
    ...    ${IP_POOL_END}
    ...    ${DEFAULT_NAMESPACE}/${VLAN_NETWORK_NAME}
    ...    ${IP_POOL_GATEWAY}
    Create Image    ${IMAGE_NAME}    ${UBUNTU_IMAGE_URL}
    Wait For Image Ready    ${IMAGE_NAME}    ${WAIT_TIMEOUT}

    Log    Test environment ready (version: ${RKE2_VERSION}, timestamp: ${timestamp})    console=yes

Import Harvester To Rancher In Setup
    [Documentation]    Import Harvester into Rancher during suite setup.
    Log    Creating Harvester management cluster: ${HARVESTER_CLUSTER_NAME}

    Create Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}

    ${cluster}=    Wait For Cluster ID    ${HARVESTER_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    ${cluster_id}=    Set Variable    ${cluster}[status][clusterName]
    Set Suite Variable    ${HARVESTER_CLUSTER_ID}    ${cluster_id}
    Log    Harvester cluster ID: ${cluster_id}

    ${manifest_url}=    Get Cluster Registration URL
    ...    ${cluster_id}    ${RANCHER_ENDPOINT}    ${RANCHER_WAIT_TIMEOUT}
    Should Not Be Empty    ${manifest_url}    Registration URL not found

    Set Cluster Registration URL    ${manifest_url}

    Wait For Harvester Ready    ${HARVESTER_CLUSTER_NAME}    ${RANCHER_WAIT_TIMEOUT}
    Log    Harvester imported successfully: ${HARVESTER_CLUSTER_NAME}

Suite Teardown For Rancher Integration Tests
    [Documentation]    Cleanup all resources after tests.
    Log    Running suite teardown

    # Cleanup clusters (best effort)
    Run Keyword And Ignore Error    Cleanup Cluster By Name    ${SINGLE_CLUSTER_NAME}
    Run Keyword And Ignore Error    Cleanup Cluster By Name    ${MULTI_CLUSTER_NAME}

    # Delete cloud credential
    Run Keyword If    '${CLOUD_CREDENTIAL_ID}' != '${EMPTY}'
    ...    Run Keyword And Ignore Error    Delete Cloud Credential    ${CLOUD_CREDENTIAL_ID}

    # Delete Harvester mgmt cluster
    Run Keyword And Ignore Error    Delete Harvester Mgmt Cluster    ${HARVESTER_CLUSTER_NAME}

    # Delete Harvester VMs
    Run Keyword And Ignore Error    Delete Harvester VM    ${IMPORT_CLUSTER_NAME}-vm-0
    Run Keyword And Ignore Error    Wait For Harvester VM Deleted    ${IMPORT_CLUSTER_NAME}-vm-0    ${RANCHER_WAIT_TIMEOUT}

    # Delete Harvester VMs shared resources
    Run Keyword And Ignore Error    Delete Image    ${IMAGE_NAME}
    Run Keyword And Ignore Error    Delete IP Pool    ${IP_POOL_NAME}
    Run Keyword And Ignore Error    Delete VLAN Network    ${VLAN_NETWORK_NAME}
    Run Keyword And Ignore Error    Delete VLAN Config    ${VLAN_CONFIG_NAME}
    Run Keyword And Ignore Error    Delete Cluster Network    ${CLUSTER_NETWORK_NAME}

    Run Keyword And Ignore Error    Set Cluster Registration URL    ${EMPTY}

    Cleanup test resources
    Log    Suite teardown completed

# ============================================================
# Utility keywords
# ============================================================
Cleanup Cluster By Name
    [Arguments]    ${cluster_name}
    [Documentation]    Delete a specific RKE2 cluster by name (best effort).
    Run Keyword And Ignore Error    Delete RKE2 Cluster    ${cluster_name}
    Run Keyword And Ignore Error    Wait For RKE2 Cluster Deleted    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}

Cleanup Custom Cluster By Name
    [Arguments]    ${cluster_name}
    [Documentation]    Delete a custom RKE2 cluster and its VMs by name (best effort).
    Run Keyword And Ignore Error    Delete RKE2 Cluster    ${cluster_name}
    Run Keyword And Ignore Error    Wait For RKE2 Cluster Deleted    ${cluster_name}    ${RANCHER_WAIT_TIMEOUT}
    Run Keyword And Ignore Error    Delete Harvester VM    ${cluster_name}-vm-0
    Run Keyword And Ignore Error    Wait For Harvester VM Deleted    ${cluster_name}-vm-0    ${RANCHER_WAIT_TIMEOUT}
