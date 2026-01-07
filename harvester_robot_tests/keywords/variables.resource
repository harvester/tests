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
${VLAN_ID}                      %{VLAN_ID=1}
${VLAN_NIC}                     %{VLAN_NIC=mgmt}

# VM Defaults
${DEFAULT_VM_CPU}               2
${DEFAULT_VM_MEMORY}            4Gi
${DEFAULT_VM_REPLICAS}          3

# Storage
${DEFAULT_STORAGE_CLASS}        longhorn
${DEFAULT_VOLUME_SIZE}          10Gi

# Test Execution
${LOOP_COUNT}                   3
${RETRY_COUNT}                  100

# Namespaces and Labels
${DEFAULT_NAMESPACE}            default
${LABEL_TEST}                   test-harvester
