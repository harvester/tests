# Harvester Robot Framework E2E Tests

This repository contains the Harvester end-to-end tests implemented using Robot Framework, following a layered architecture pattern.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Kubernetes Configuration (CRD Setup)](#kubernetes-configuration-crd-setup)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Writing New Tests](#writing-new-tests)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)

## Overview

The Harvester Robot Framework test suite provides comprehensive end-to-end testing for Harvester HCI, including:

- Virtual machine lifecycle management
- Image operations (upload, download, management)
- Volume operations and storage management
- Network configuration (VLAN, cluster networks)
- Backup and restore operations
- Node management and HA scenarios
- Rancher integration testing
- Upgrade scenarios

### Implementation Strategies

This test framework supports **two implementation strategies**:

1. **CRD (Kubernetes Custom Resources)** - Default ✅
   - Uses Kubernetes APIs directly
   - Works with KubeVirt and Harvester CRDs
   - Requires direct cluster access
   
2. **REST (Harvester REST API)** - Alternative
   - Uses Harvester REST API endpoints
   - Suitable for remote testing
   - Set `HARVESTER_OPERATION_STRATEGY=rest` to use

## Architecture

The test framework follows a strict 4-layer architecture:

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 1: tests/*.robot - Test Case Definition                  │
│  - Define test scenarios and workflows                         │
│  - Import Layer 2 resource files                               │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Layer 2: keywords/*.resource - Keyword Definition              │
│  - Define reusable keywords                                    │
│  - Import Layer 3 Python keyword libraries                     │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Layer 3: libs/keywords/*_keywords.py - Keyword Wrappers        │
│  - Create component instances                                  │
│  - Delegate to Layer 4 components                              │
│  - NO direct API calls                                         │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Layer 4: libs/{vm,image,host,volume}/*.py - Components         │
│  - Component wrapper: delegates to CRD or REST implementation  │
│  - CRD/REST implementation: makes actual API calls             │
│  - Base: abstract base classes                                 │
└────────────────────────────────────────────────────────────────┘
```

**Important**: Each layer can ONLY call functions from the next layer or the same layer. Skip-layer dependencies are strictly forbidden.

## Requirements

### Prerequisites

1. A running Harvester cluster
2. Python 3.8 or higher
3. `kubectl` configured with access to the cluster (for CRD strategy)
4. Access to Harvester API endpoint (for REST strategy)
5. Kubernetes credentials configured in kubeconfig

### Optional Requirements

For specific test scenarios:

- **Network Tests**: VLAN configuration with proper routing and DHCP
- **Backup Tests**: S3-compatible storage or NFS server
- **Node Management Tests**: Node power management scripts
- **Rancher Integration Tests**: External Rancher cluster

## Installation

1. Clone the repository:
```bash
git clone https://github.com/harvester/harvester-robot-tests.git
cd harvester-robot-tests
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Kubernetes Configuration (CRD Setup)

### Default Strategy: CRD (Kubernetes Custom Resources)

The test framework uses **CRD strategy by default**. This requires Kubernetes cluster access.

### Step 1: Get Kubeconfig from Harvester Cluster

#### From Harvester UI
1. Login to Harvester Dashboard
2. Go to `Support`
3. Click `Download Kubeconfig`
4. Save the file

#### From Harvester Command Line
```bash
# SSH into a Harvester node
ssh rancher@<harvester-ip>

# Get the kubeconfig
sudo cat /etc/rancher/rke2/rke2.yaml | sed 's/127.0.0.1/<HARVESTER_IP>/g'
```

### Step 2: Set Up Kubeconfig

#### Option A: Using Default Kubeconfig Location

```bash
# The default location is $HOME/.kube/config
# Copy your cluster's kubeconfig here:

mkdir -p $HOME/.kube
cp /path/to/your/harvester-kubeconfig.yaml $HOME/.kube/config
chmod 600 $HOME/.kube/config

# Verify access:
kubectl get nodes
```

#### Option B: Using Custom Kubeconfig Location

```bash
# Export the path:
export KUBECONFIG=/path/to/your/kubeconfig.yaml

# Or set it permanently in shell profile:
echo 'export KUBECONFIG=/path/to/your/kubeconfig.yaml' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Verify Kubernetes Access

Before running tests, verify that kubectl can communicate with the cluster:

```bash
# Check nodes
kubectl get nodes
# Expected output: Should show your cluster nodes
```

### Step 4: Configure Test Strategy

#### For CRD Strategy (Default)
```bash
# Set environment variable to use CRD (default)
export HARVESTER_OPERATION_STRATEGY=crd

# Or set in .env file:
echo "HARVESTER_OPERATION_STRATEGY=crd" >> .env
```

#### For REST Strategy (Alternative)
```bash
# Set environment variable to use REST API
export HARVESTER_OPERATION_STRATEGY=rest

# Or set in .env file:
echo "HARVESTER_OPERATION_STRATEGY=rest" >> .env
```

## Configuration

### Quick Start with .env File (Recommended)

The easiest way to configure the test environment is using the `.env` file:

```bash
# 1. Copy the example configuration file
cp .env.example .env

# 2. Edit .env with your cluster details
vi .env

# 3. Update at minimum these variables:
#    HARVESTER_ENDPOINT=https://your-harvester-ip
#    HARVESTER_USERNAME=admin
#    HARVESTER_PASSWORD=your-password
#    KUBECONFIG=/path/to/your/kubeconfig  # Optional, defaults to ~/.kube/config

# 4. The run.sh script will automatically load these variables
```

### Environment Variables Reference

The `.env.example` file contains all available configuration options:

#### Required Variables (for CRD strategy):
- `KUBECONFIG` - Path to kubeconfig file (defaults to `~/.kube/config`)

#### Optional Variables:
- `HARVESTER_ENDPOINT` - Harvester API endpoint
- `HARVESTER_USERNAME` - Admin username
- `HARVESTER_PASSWORD` - Admin password
- `VLAN_ID` - VLAN ID for network tests
- `VLAN_NIC` - Network interface for VLAN (default: `mgmt`)
- `ROBOT_LOG_LEVEL` - Test log level (default: `INFO`)
- `ROBOT_OUTPUT_DIR` - Output directory for results (default: `./results`)

### Manual Configuration (Alternative)

If you prefer not to use the `.env` file, you can set environment variables manually:

```bash
# Kubernetes configuration (for CRD strategy)
export KUBECONFIG=$HOME/.kube/config
export HARVESTER_OPERATION_STRATEGY=crd

# Harvester cluster info (optional for CRD, required for REST)
export HARVESTER_ENDPOINT="https://your-harvester-ip"
export HARVESTER_USERNAME="admin"
export HARVESTER_PASSWORD="your-password"

# Test configuration
export WAIT_TIMEOUT=600
```

### Configure Test Variables

Robot Framework variables are defined in `keywords/variables.resource`. These variables:
- Use environment variables when available (via `%{VAR_NAME=default}` syntax)
- Fall back to sensible defaults if environment variables are not set
- Can be overridden at runtime using `-v` flag

## Running Tests

### Option 1: Using run.sh Script (Recommended)

The `run.sh` script automatically loads `.env` configuration and provides convenient options:

```bash
# Run all tests (with .env configuration)
./run.sh

# Run specific test file
./run.sh -f tests/regression/test_vm.robot

# Run specific test suite by name
./run.sh -s test_vm

# Run specific test case by name
./run.sh -t "Test VM Basic Lifecycle"

# Run with specific tags
./run.sh -i coretest              # Include tests tagged 'coretest'
./run.sh -i p0 -e backup          # Include p0, exclude backup tests

# Run with debug logging
./run.sh -L DEBUG

# Run with custom output directory
./run.sh -d ./my-results

# Set custom variable
./run.sh -v WAIT_TIMEOUT:1200

# Show help
./run.sh -h
```

**Note**: The `run.sh` script automatically:
- Loads environment variables from `.env` file if it exists
- Sets up Python path to include the libs directory
- Creates output directory if it doesn't exist
- Provides colored console output
- Shows configuration summary before running tests

### Option 2: Using Robot Command Directly

If you prefer to use the `robot` command directly:

```bash
# Run all tests
robot tests/

# Run specific test suite
robot tests/regression/test_vm.robot

# Run specific test case
robot --test "Test VM Basic Lifecycle" tests/regression/test_vm.robot

# Run with debug logging
robot --loglevel DEBUG tests/regression/test_vm.robot

# Run with tags
robot --include smoke tests/
robot --exclude slow tests/

# Dry run (syntax validation)
robot --dryrun tests/regression/test_vm.robot

# Run with custom variables
robot --variable WAIT_TIMEOUT:1200 tests/

# Generate reports in custom directory
robot --outputdir results/ tests/
```

## Test Reports

After test execution, reports are generated in the `results/` directory:

```
results/
└── YYYYMMDD_HHMMSS/
    ├── report.html         # High-level test execution summary
    ├── log.html            # Detailed execution log
    └── output.xml          # Machine-readable test results (for CI/CD)
```

## Writing New Tests

### Test File Structure

Create a new test file in `tests/regression/` or `tests/negative/`:

```robot
*** Settings ***
Documentation    Description of your test suite
Test Tags        regression    your-category

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/virtualmachine.resource

Test Setup       Set up test environment
Test Teardown    Cleanup test resources

*** Test Cases ***
Your Test Case Name
    [Tags]    p0    coretest    smoke
    [Documentation]    Detailed description of what this test does
    
    Given Setup preconditions
    When Perform action
    Then Verify expected result
```

### Adding New Keywords

1. Define keywords in `keywords/*.resource`:
```robot
*** Keywords ***
My Custom Keyword
    [Arguments]    ${arg1}    ${arg2}
    Log    Doing something with ${arg1} and ${arg2}
    my_python_keyword    ${arg1}    ${arg2}
```

2. Implement in `libs/keywords/*_keywords.py`:
```python
class MyKeywords:
    def __init__(self):
        self.component = MyComponent()
    
    def my_python_keyword(self, arg1, arg2):
        return self.component.do_something(arg1, arg2)
```

### Test Tags

Use appropriate tags for your tests:

- **Priority**: `p0` (critical), `p1` (high), `p2` (medium), `p3` (low)
- **Category**: `coretest`, `regression`, `negative`, `sanity`
- **Component**: `virtualmachines`, `images`, `volumes`, `networks`, `backup`, `ha`
- **Speed**: `smoke` (quick), `slow` (long-running)
- **Scope**: `unit`, `integration`, `e2e`

### Best Practices

1. **Layer Discipline**: Never skip layers when calling functions
2. **Test Independence**: Each test should be self-contained
3. **Descriptive Names**: Use clear, descriptive names
4. **Documentation**: Document test purpose, steps, and expected results
5. **Cleanup**: Always clean up resources in teardown
6. **Unique Names**: Use generated unique names to avoid conflicts
7. **Proper Tagging**: Tag tests appropriately for selective execution
8. **Assertions**: Use explicit assertions to verify expected behavior
9. **Logging**: Use logging for debugging and understanding test flow
10. **Timeout Handling**: Always set appropriate timeouts for async operations

## Directory Structure

```
harvester_robot_tests/
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── run.sh                           # Test runner script
├── Dockerfile
├── .env.example                     # Example environment file
├── keywords/                        # Layer 2: Resource files
│   ├── variables.resource
│   ├── common.resource
│   ├── virtualmachine.resource
│   ├── image.resource
│   ├── volume.resource
│   ├── network.resource
│   └── ...
├── libs/                            # Layers 3 & 4: Python implementation
│   ├── keywords/                    # Layer 3: Keyword wrappers
│   │   ├── vm_keywords.py
│   │   ├── image_keywords.py
│   │   └── ...
│   ├── vm/                          # Layer 4: VM component
│   │   ├── vm.py                    # Component wrapper
│   │   ├── crd.py                   # CRD implementation ✨
│   │   ├── rest.py                  # REST implementation
│   │   └── base.py
│   ├── image/
│   ├── utility/
│   └── ...
├── scripts/
│   └── node-management/
└── tests/                           # Layer 1: Test cases
    ├── regression/
    └── negative/
```

## Troubleshooting

### Kubeconfig Issues

**Error: `Unable to connect to cluster`**

```bash
# Verify kubeconfig path
echo $KUBECONFIG

# Set correct kubeconfig
export KUBECONFIG=$HOME/.kube/config

# Verify access
kubectl get nodes
```

**Error: `No kubeconfig found`**

```bash
# Check if kubeconfig exists
ls -la $HOME/.kube/config

# If not, get from Harvester:
# 1. Via Harvester UI: Cluster > Local > Kubeconfig
# 2. Or SSH to node and get it
```

### CRD Strategy Issues

**Error: `connection refused` when using CRD**

```bash
# Verify you have direct cluster access
kubectl cluster-info

# Verify KubeVirt CRDs exist
kubectl get crd | grep kubevirt

# Check Kubernetes version (should be 1.18+)
kubectl version
```

**Error: `Permission denied` creating VMs**

```bash
# Verify RBAC permissions
kubectl auth can-i create virtualmachines --namespace=default

# Check service account
kubectl get serviceaccount -n default
```

### Tests Fail to Connect to Harvester

- Verify `HARVESTER_ENDPOINT` is correct (for REST strategy)
- Check credentials are valid
- Ensure network connectivity from test machine to cluster
- Verify firewall rules allow access to API endpoint

### Image Download Timeouts

- Increase `WAIT_TIMEOUT` variable
- Use `image_cache_url` to serve images from local cache
- Check network bandwidth and firewall rules

## Contributing

When contributing new tests:

1. Follow the 4-layer architecture strictly
2. Add appropriate documentation and tags
3. Ensure tests clean up all resources
4. Test locally before submitting
5. Update this README if adding new features
6. For CRD strategy, test with `kubectl` access
7. For REST strategy, test with API credentials
