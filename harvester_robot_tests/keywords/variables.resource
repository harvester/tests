*** Settings ***
Documentation    Global Variables for Harvester Robot Tests
Library          Collections
Library          String  
Library          DateTime

*** Variables ***
# Harvester Cluster
${HARVESTER_ENDPOINT}           %{HARVESTER_ENDPOINT=https://localhost}
${HARVESTER_USERNAME}           %{HARVESTER_USERNAME=admin}
${HARVESTER_PASSWORD}           %{HARVESTER_PASSWORD=password}

# Timeouts and Intervals
${WAIT_TIMEOUT}                 600
${RETRY_INTERVAL}               3
${SLEEP_TIMEOUT}                3

# Images
${OPENSUSE_IMAGE_URL}           https://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.6/images/openSUSE-Leap-15.6.x86_64-NoCloud.qcow2
${UBUNTU_IMAGE_URL}             https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img

# Network
${VLAN_ID}                      %{VLAN_ID=2011}
${VLAN_NIC}                     %{VLAN_NIC=eno50}

# VM Defaults
${DEFAULT_VM_CPU}               2
${DEFAULT_VM_MEMORY}            4Gi
${DEFAULT_VM_REPLICAS}          3

# Storage
${DEFAULT_STORAGE_CLASS}        harvester-longhorn
${DEFAULT_VOLUME_SIZE}          10Gi
${RWX_HOST_STORAGE_CLASS}       %{RWX_HOST_STORAGE_CLASS=longhorn-rwx}

# Test Execution
${LOOP_COUNT}                   3
${RETRY_COUNT}                  100

# Namespaces and Labels
${DEFAULT_NAMESPACE}            default
${LABEL_TEST}                   test-harvester

# NVIDIA Driver Toolkit Addon
${NVIDIA_TOOLKIT_IMAGE_REPO}    %{NVIDIA_TOOLKIT_IMAGE_REPO=nvidia/driver-toolkit}
${NVIDIA_TOOLKIT_IMAGE_TAG}     %{NVIDIA_TOOLKIT_IMAGE_TAG=v1.7-20260209}
${NVIDIA_TOOLKIT_DRIVER_LOCATION}   %{NVIDIA_TOOLKIT_DRIVER_LOCATION=http://HTTPENDPOINT/NVIDIA-Linux-x86_64-VERSION-vgpu-kvm.run}

# Rancher Integration
${RANCHER_ENDPOINT}             %{RANCHER_ENDPOINT=https://rancher.localhost}
${RANCHER_USERNAME}             %{RANCHER_USERNAME=admin}
${RANCHER_PASSWORD}             %{RANCHER_PASSWORD=password}
${RANCHER_WAIT_TIMEOUT}         1200

# RKE2 Version Configuration
${RKE2_VERSION}                %{RKE2_VERSION=v1.34}

# Ingress Controller: traefik (default, recommended by Rancher) or nginx
${INGRESS_CONTROLLER}           %{INGRESS_CONTROLLER=traefik}

# Chart Repository for import clusters
${CHART_REPO_URL}               %{CHART_REPO_URL=https://github.com/rancher/charts}
${CHART_REPO_BRANCH}            %{CHART_REPO_BRANCH=release-v2.14}

# IP Pool for LoadBalancer tests
${IP_POOL_SUBNET}               %{IP_POOL_SUBNET=192.168.1.0/24}
${IP_POOL_START}                %{IP_POOL_START=192.168.1.100}
${IP_POOL_END}                  %{IP_POOL_END=192.168.1.200}
