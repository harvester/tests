# Copilot Instructions for Harvester Test Development

## Overview
This document provides guidelines for GitHub Copilot to assist with test development in the Harvester test suite. The repository contains two main test frameworks: pytest and Robot Framework.

## 1. Adding Test Cases in Pytest Framework

### Location
- **Directory**: `tests/harvester_e2e_tests/`
- **Integration tests**: `tests/harvester_e2e_tests/integrations/`
- **Test fixtures**: `tests/harvester_e2e_tests/fixtures/`

### Pytest Test Structure

```python
import pytest
from time import sleep
from datetime import datetime, timedelta

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",
    "harvester_e2e_tests.fixtures.networks",
]

@pytest.mark.p0  # or p1 for priority
@pytest.mark.experimental  # if testing experimental features
class TestFeatureName:
    """
    Test Feature functionality
    
    Description of what this test class covers
    """
    
    @pytest.mark.dependency(name="feature_setup")
    def test_setup_feature(self, api_client, wait_timeout):
        """
        Test setting up the feature
        
        Steps:
            1. Step one description
            2. Step two description
            3. Step three description
        
        Expected Result:
            - Expected outcome 1
            - Expected outcome 2
        """
        # Test implementation
        pass
    
    @pytest.mark.dependency(depends=["feature_setup"])
    def test_verify_feature(self, api_client, wait_timeout):
        """
        Test verifying the feature works correctly
        
        Steps:
            1. Verify step one
            2. Verify step two
        
        Expected Result:
            - Feature should work as expected
        """
        # Test implementation
        pass
    
    def test_cleanup_feature(self, api_client, wait_timeout):
        """
        Test cleaning up feature resources
        """
        # Cleanup implementation
        pass
```

### Pytest Guidelines

1. **Imports**: Import required modules at the top
   ```python
   from time import sleep
   from datetime import datetime, timedelta
   import subprocess
   import tempfile
   import os
   import json
   import pytest
   import requests
   ```

2. **Test Markers**: Use appropriate pytest markers
   - `@pytest.mark.p0` - Critical/high priority tests
   - `@pytest.mark.p1` - Medium priority tests
   - `@pytest.mark.experimental` - Experimental features
   - `@pytest.mark.addons` - Addon-related tests
   - `@pytest.mark.dependency(name="test_name")` - Define test dependencies

3. **Fixtures**: Common fixtures available
   - `api_client` - Harvester API client
   - `wait_timeout` - Default timeout for operations
   - `image_opensuse` - OpenSUSE image configuration
   - `unique_name` - Generate unique names for resources
   - `vlan_id` - VLAN ID for network tests
   - `request` - pytest request object for config access

4. **API Client Usage**:
   ```python
   # Get resource
   code, data = api_client.resource.get(resource_id)
   
   # Create resource
   code, data = api_client.resource.create(name, params)
   
   # Delete resource
   code, data = api_client.resource.delete(name)
   
   # Enable/disable addons
   code, data = api_client.addons.enable(addon_id)
   code, data = api_client.addons.disable(addon_id)
   ```

5. **Timeout Pattern**:
   ```python
   endtime = datetime.now() + timedelta(seconds=wait_timeout)
   while endtime > datetime.now():
       code, data = api_client.resource.get(resource_name)
       if code == 200 and data.get('status') == 'ready':
           break
       sleep(5)
   else:
       raise AssertionError(f"Resource did not become ready within {wait_timeout} seconds")
   ```

6. **Cleanup Pattern**:
   ```python
   try:
       # Test operations
       pass
   finally:
       # Cleanup resources
       try:
           code, data = api_client.resource.delete(resource_name)
       except Exception as e:
           print(f"Warning: Cleanup failed: {e}")
   ```

7. **Docstrings**: Always include comprehensive docstrings
   - Test class: Describe feature being tested
   - Test method: Include Steps and Expected Result sections

8. **Code Quality**:
   - Follow PEP 8 guidelines (max line length: 99 characters)
   - Use meaningful variable names
   - Add comments for complex logic
   - Handle exceptions appropriately
   - Use `pytest.skip()` for missing prerequisites

### Creating New Harvester API Managers

When adding support for a new Harvester resource that doesn't already exist, you need to create an API manager.

#### Step 1: When to Create a New API Manager

Before creating a new API manager:

1. **Search for existing implementations** (use plural form of resource name):
   ```bash
   ls apiclient/harvester_api/managers/
   # Look for: images.py, storageclasses.py, virtualmachines.py, etc.
   ```

2. **Search by resource name**:
   - Example: For resource "noodle", search for `noodle` or `noodles`
   - Only check `harvester_api/managers/`, NOT `rancher_api/`

3. **API managers are used in**:
   - Integration tests (`harvester_e2e_tests/integrations/`)
   - API tests (`harvester_e2e_tests/apis/`)

#### Step 2: Create API Manager

**Location**: `apiclient/harvester_api/managers/{resource_plural}.py`

```python
"""
{Resource} API Manager
Handles CRUD operations for {resource} resources in Harvester
"""

import base64
from .base import BaseManager, DEFAULT_NAMESPACE


class {Resource}sManager(BaseManager):
    """
    Manager for {resource} resources
    
    Provides methods to create, get, update, and delete {resource} resources
    through the Harvester API.
    """
    
    # API path template for individual resource operations
    PATH_fmt = "/v1/harvester/{api_group}/{resource_plural}/{ns}/{name}"
    
    # API path for creating resources
    CREATE_fmt = "v1/harvester/{api_group}/{resource_plural}"
    
    def create_data(self, name, namespace, spec_data, annotations=None, labels=None):
        """
        Build the request payload for creating a resource
        
        Args:
            name: Resource name
            namespace: Kubernetes namespace
            spec_data: Resource-specific specification data
            annotations: Optional metadata annotations
            labels: Optional metadata labels
            
        Returns:
            dict: Complete resource manifest
        """
        data = {
            "type": "{api_group}.{resource}",
            "metadata": {
                "namespace": namespace,
                "name": name,
            },
            "spec": spec_data
        }
        
        if annotations:
            data["metadata"]["annotations"] = annotations
        
        if labels:
            data["metadata"]["labels"] = labels
        
        return data
    
    def create(self, name, spec_data, namespace=DEFAULT_NAMESPACE, 
               annotations=None, labels=None, **kwargs):
        """
        Create a new resource
        
        Args:
            name: Resource name
            spec_data: Resource specification
            namespace: Kubernetes namespace (default: DEFAULT_NAMESPACE)
            annotations: Optional annotations
            labels: Optional labels
            **kwargs: Additional arguments passed to HTTP request
            
        Returns:
            tuple: (status_code, response_data)
            
        Example:
            code, data = api_client.resources.create(
                name="my-resource",
                spec_data={"key": "value"},
                namespace="default"
            )
            assert code == 201, f"Expected 201, got {code}"
        """
        payload = self.create_data(
            name, namespace, spec_data, 
            annotations=annotations, labels=labels
        )
        return self._create(self.CREATE_fmt, json=payload, **kwargs)
    
    def get(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        """
        Get a resource by name
        
        Args:
            name: Resource name
            namespace: Kubernetes namespace
            raw: If True, return raw response object
            
        Returns:
            tuple: (status_code, response_data)
            
        Example:
            code, data = api_client.resources.get("my-resource")
            assert code == 200, f"Expected 200, got {code}"
        """
        path = self.PATH_fmt.format(ns=namespace, name=name)
        return self._get(path, raw=raw)
    
    def update(self, name, spec_data, namespace=DEFAULT_NAMESPACE, **kwargs):
        """
        Update an existing resource
        
        Args:
            name: Resource name
            spec_data: Updated resource specification
            namespace: Kubernetes namespace
            **kwargs: Additional arguments
            
        Returns:
            tuple: (status_code, response_data)
        """
        # First get the current resource
        code, current_data = self.get(name, namespace)
        if code != 200:
            return code, current_data
        
        # Update the spec
        current_data["spec"].update(spec_data)
        
        # Send update
        path = self.PATH_fmt.format(ns=namespace, name=name)
        return self._update(path, json=current_data, **kwargs)
    
    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        """
        Delete a resource
        
        Args:
            name: Resource name
            namespace: Kubernetes namespace
            raw: If True, return raw response object
            
        Returns:
            tuple: (status_code, response_data)
            
        Example:
            code, data = api_client.resources.delete("my-resource")
            assert code == 200, f"Expected 200, got {code}"
        """
        path = self.PATH_fmt.format(ns=namespace, name=name)
        return self._delete(path, raw=raw)
    
    def list(self, namespace=DEFAULT_NAMESPACE, **kwargs):
        """
        List all resources in namespace
        
        Args:
            namespace: Kubernetes namespace
            **kwargs: Additional query parameters
            
        Returns:
            tuple: (status_code, response_data)
        """
        path = f"/v1/harvester/{{api_group}}/{{resource_plural}}/{namespace}"
        return self._get(path, **kwargs)
```

**Real Example - Images Manager**:

```python
"""Images API Manager"""

from .base import BaseManager, DEFAULT_NAMESPACE


class ImagesManager(BaseManager):
    PATH_fmt = "v1/harvester/harvesterhci.io.virtualmachineimages/{ns}/{name}"
    
    def create(self, name, url, namespace=DEFAULT_NAMESPACE, 
               display_name="", description="", source_type="download", **kwargs):
        """Create a new image"""
        data = {
            "type": "harvesterhci.io.virtualmachineimage",
            "metadata": {
                "annotations": {
                    "field.cattle.io/description": description
                },
                "name": name,
                "namespace": namespace
            },
            "spec": {
                "displayName": display_name or name,
                "sourceType": source_type,
                "url": url
            }
        }
        return self._create(self.PATH_fmt.format(ns=namespace, name=name), json=data)
    
    def get(self, name="", namespace=DEFAULT_NAMESPACE, *, raw=False):
        """Get image(s)"""
        return self._get(self.PATH_fmt.format(ns=namespace, name=name), raw=raw)
    
    def delete(self, name, namespace=DEFAULT_NAMESPACE):
        """Delete an image"""
        return self._delete(self.PATH_fmt.format(ns=namespace, name=name))
```

#### Step 3: Register API Manager

After creating the manager, register it in two places:

**1. Load in `apiclient/harvester_api/api.py`**:

```python
from harvester_api.managers import (
    # ... existing imports ...
    ResourcesManager,  # Add your new manager
)

class HarvesterAPI:
    def load_managers(self, cluster_version):
        # ... existing managers ...
        self.resources = ResourcesManager(self.session)  # Register your manager
```

**2. Export in `apiclient/harvester_api/managers/__init__.py`**:

```python
from .resources import ResourcesManager  # Import your manager

__all__ = [
    # ... existing exports ...
    "ResourcesManager",  # Export your manager
]
```

### Writing Integration and API Tests

#### Test Structure

**Integration Tests** (`harvester_e2e_tests/integrations/`):
- Test complete workflows and feature interactions
- Example: `test_1_images.py`, `test_3_vm_functions.py`

**API Tests** (`harvester_e2e_tests/apis/`):
- Test individual API endpoints
- Example: `test_images.py`, `test_volumes.py`

#### Test Requirements

**CRITICAL**: Every test class must include:
1. ✅ At least one **positive test case** (success scenario)
2. ✅ At least one **negative test case** (failure scenario)

#### Standard HTTP Status Codes

Follow these conventions when validating Harvester API responses:

```python
# Success cases
assert code == 201, f"Expected 201 (Created), got {code}"      # Resource created
assert code == 200, f"Expected 200 (OK), got {code}"           # Operation succeeded

# Failure cases
assert code == 422, f"Expected 422 (Unprocessable), got {code}"  # Operation failed
assert code == 404, f"Expected 404 (Not Found), got {code}"      # Resource not found
assert code == 409, f"Expected 409 (Conflict), got {code}"       # Resource conflict
```

### Test Templates

#### Shared Fixture Template

Use module or class-scoped fixtures for resources shared across tests:

```python
@pytest.fixture(scope="module")  # or "class"
def shared_image(api_client, unique_name, wait_timeout):
    """
    Shared fixture that creates an image for multiple tests
    
    Yields:
        dict: Image data including name, url, and metadata
    """
    # 1. Prepare the environment and data
    image_name = f"test-image-{unique_name}"
    image_url = "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img"
    
    code, data = api_client.images.create(
        name=image_name,
        url=image_url,
        display_name="Test Image"
    )
    
    # 2. Assert the result
    assert code == 201, f"Expected status code 201, got {code} with data: {data}"
    
    # 3. Wait for image to be ready
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(image_name)
        if code == 200 and data.get('status', {}).get('progress') == 100:
            break
        sleep(10)
    else:
        raise AssertionError(f"Image {image_name} not ready within {wait_timeout}s")
    
    # 4. Prepare output data
    output = {
        "name": image_name,
        "url": image_url,
        "data": data
    }
    
    yield output
    
    # 5. Teardown - cleanup the image
    code, data = api_client.images.delete(image_name)
    # Note: Don't assert in teardown, just log if cleanup fails
    if code not in [200, 204, 404]:
        print(f"Warning: Failed to delete image {image_name}: {code}")
```

#### Positive Test Case Template

```python
@pytest.mark.p0
@pytest.mark.images
@pytest.mark.skip_version_if("< v1.2.0", reason="Feature added in v1.2.0")
class TestImageOperations:
    """
    Test image creation, retrieval, and deletion operations
    
    This test class validates the basic CRUD operations for VM images,
    ensuring they can be created from URLs, retrieved, and deleted properly.
    """
    
    @pytest.mark.dependency(name="create_image")
    def test_create_image_success(self, api_client, unique_name, wait_timeout):
        """
        Test successful image creation from URL
        
        Steps:
            1. Create an image with valid URL
            2. Verify response status is 201
            3. Wait for image to complete download
            4. Verify image status is Active
            5. Cleanup the image
            
        Expected Result:
            - Image is created successfully
            - Image reaches Active state within timeout
        """
        # 1. Prepare test data
        image_name = f"test-image-{unique_name}"
        image_url = "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img"
        
        # 2. Call the API
        code, data = api_client.images.create(
            name=image_name,
            url=image_url,
            display_name="Ubuntu 20.04"
        )
        
        # 3. Assert creation response
        assert code == 201, f"Expected status code 201, got {code} with data: {data}"
        assert data['metadata']['name'] == image_name
        
        try:
            # 4. Wait for image to be ready
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                code, data = api_client.images.get(image_name)
                assert code == 200, f"Failed to get image: {code}"
                
                if data.get('status', {}).get('progress') == 100:
                    break
                sleep(10)
            else:
                raise AssertionError(f"Image not ready within {wait_timeout}s")
            
            # 5. Verify final state
            assert data['status']['conditions'][0]['status'] == 'True'
            
        finally:
            # 6. Cleanup
            code, data = api_client.images.delete(image_name)
```

#### Negative Test Case Template

```python
@pytest.mark.p0
@pytest.mark.images
@pytest.mark.negative
class TestImageNegative:
    """
    Test image operations failure scenarios
    
    Validates that the API properly handles invalid inputs and
    returns appropriate error codes.
    """
    
    def test_create_image_invalid_url(self, api_client, unique_name):
        """
        Test image creation fails with invalid URL
        
        Steps:
            1. Attempt to create image with invalid URL
            2. Verify response status is 422 (Unprocessable Entity)
            3. Verify error message indicates invalid URL
            
        Expected Result:
            - Image creation fails with 422 status
            - Error message is descriptive
        """
        # 1. Prepare invalid data
        image_name = f"test-invalid-{unique_name}"
        invalid_url = "not-a-valid-url"
        
        # 2. Call the API with invalid data
        code, data = api_client.images.create(
            name=image_name,
            url=invalid_url
        )
        
        # 3. Assert failure response
        assert code == 422, (
            f"Expected status code 422 for invalid URL, got {code} with data: {data}"
        )
        
        # Optional: Verify no resource was created
        code, data = api_client.images.get(image_name)
        assert code == 404, "Image should not exist after failed creation"
    
    def test_delete_nonexistent_image(self, api_client):
        """
        Test deletion of non-existent image
        
        Steps:
            1. Attempt to delete an image that doesn't exist
            2. Verify response status is 404 (Not Found)
            
        Expected Result:
            - Deletion fails with 404 status
        """
        # 1. Attempt to delete non-existent resource
        code, data = api_client.images.delete("nonexistent-image-12345")
        
        # 2. Assert failure response
        assert code == 404, (
            f"Expected status code 404 for non-existent image, got {code}"
        )
    
    def test_create_duplicate_image(self, api_client, unique_name):
        """
        Test creating image with duplicate name fails
        
        Steps:
            1. Create an image
            2. Attempt to create another image with same name
            3. Verify second creation fails with 409 (Conflict)
            4. Cleanup
            
        Expected Result:
            - First creation succeeds
            - Second creation fails with conflict error
        """
        image_name = f"test-duplicate-{unique_name}"
        image_url = "https://releases.rancher.com/os/latest/rancheros.iso"
        
        # 1. Create first image
        code, data = api_client.images.create(name=image_name, url=image_url)
        assert code == 201, f"First creation should succeed, got {code}"
        
        try:
            # 2. Attempt duplicate creation
            code, data = api_client.images.create(name=image_name, url=image_url)
            
            # 3. Assert conflict response
            assert code == 409, (
                f"Expected status code 409 for duplicate image, got {code}"
            )
        finally:
            # 4. Cleanup
            api_client.images.delete(image_name)
```

#### Test Class with Dependencies

```python
@pytest.mark.p0
@pytest.mark.volumes
class TestVolumeLifecycle:
    """
    Test volume lifecycle with dependent operations
    
    Uses pytest.mark.dependency to ensure tests run in order
    and share state through a fixture.
    """
    
    @pytest.mark.dependency(name="create_volume")
    def test_create_volume(self, api_client, unique_name, volume_state):
        """Create a volume and store its name"""
        volume_name = f"test-vol-{unique_name}"
        
        code, data = api_client.volumes.create(
            name=volume_name,
            size="10Gi"
        )
        
        assert code == 201, f"Expected 201, got {code}"
        volume_state.name = volume_name
    
    @pytest.mark.dependency(name="get_volume", depends=["create_volume"])
    def test_get_volume(self, api_client, volume_state):
        """Retrieve the created volume"""
        code, data = api_client.volumes.get(volume_state.name)
        
        assert code == 200, f"Expected 200, got {code}"
        assert data['spec']['resources']['requests']['storage'] == "10Gi"
    
    @pytest.mark.dependency(depends=["get_volume"])
    def test_delete_volume(self, api_client, volume_state):
        """Delete the volume"""
        code, data = api_client.volumes.delete(volume_state.name)
        
        assert code == 200, f"Expected 200, got {code}"


@pytest.fixture(scope="class")
def volume_state():
    """Fixture to share volume state across tests"""
    class VolumeState:
        name = None
    return VolumeState()
```

### Best Practices for API Managers

1. **Naming Convention**:
   - File: `{resource_plural}.py` (e.g., `images.py`, `volumes.py`)
   - Class: `{Resource}sManager` (e.g., `ImagesManager`, `VolumesManager`)

2. **Method Naming**:
   - Use standard CRUD names: `create`, `get`, `update`, `delete`, `list`
   - Add resource-specific methods as needed (e.g., `start`, `stop` for VMs)

3. **Don't Use Private Methods**:
   ```python
   # ❌ WRONG - Don't use underscore prefix for public APIs
   def _create_data(self, ...):  # This suggests private method
       pass
   
   # ✅ CORRECT - Public helper methods
   def create_data(self, ...):   # Available for users
       pass
   
   # ✅ CORRECT - Use underscore only for truly internal helpers
   def _build_url(self, ...):    # Only used internally
       pass
   ```

4. **Extend, Don't Duplicate**:
   ```python
   # ✅ CORRECT - Add parameters to extend functionality
   def create(self, name, spec, labels=None, annotations=None, **kwargs):
       # Handle all cases with parameters
       pass
   
   # ❌ WRONG - Don't create separate method for variations
   def create_with_labels(self, name, spec, labels):
       pass
   ```

5. **Consistent Return Format**:
   - Always return `(status_code, response_data)` tuple
   - Use `raw=False` parameter for parsed JSON vs raw response

6. **Error Handling**:
   - Let HTTP errors bubble up naturally
   - Don't catch and re-raise without adding value
   - Document expected status codes in docstrings

## 2. Adding Test Cases in Robot Framework

### Overview

The Robot Framework tests follow a **strict 4-layer architecture**. Understanding and respecting this architecture is **CRITICAL** for maintainability and consistency.

**GOLDEN RULE**: Each layer can ONLY call functions from the next layer or the same layer. **Skip-layer dependencies are strictly forbidden.**

### Location
- **Base Directory**: `harvester_robot_tests/`
- **Layer 1 (Tests)**: `harvester_robot_tests/tests/regression/` or `tests/negative/`
- **Layer 2 (Keywords)**: `harvester_robot_tests/keywords/*.resource`
- **Layer 3 (Wrappers)**: `harvester_robot_tests/libs/keywords/*_keywords.py`
- **Layer 4 (Components)**: `harvester_robot_tests/libs/{vm,image,volume,host}/`

### 4-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: tests/*.robot - Test Case Definition                   │
│  ✅ Define test scenarios and workflows                          │
│  ✅ Import Layer 2 resource files                                │
│  ✅ Call keywords from Layer 2                                   │
│  ❌ NEVER import Python libraries                                │
│  ❌ NEVER call Layer 3 or Layer 4 directly                       │
└─────────────────────────────────────────────────────────────────┘
                          ↓ ONLY
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: keywords/*.resource - Keyword Definition               │
│  ✅ Define reusable keywords                                     │
│  ✅ Import Layer 3 Python keyword libraries                      │
│  ✅ Call Layer 3 keyword wrapper functions                       │
│  ❌ NEVER import Layer 4 component files                         │
│  ❌ NEVER make API calls or kubectl commands                     │
└─────────────────────────────────────────────────────────────────┘
                          ↓ ONLY
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: libs/keywords/*_keywords.py - Keyword Wrappers         │
│  ✅ Create Layer 4 component instances                           │
│  ✅ Delegate ALL operations to Layer 4 components                │
│  ✅ Handle Robot Framework integration                           │
│  ❌ NEVER make direct API calls                                  │
│  ❌ NEVER use kubectl, requests, or kubernetes client directly   │
└─────────────────────────────────────────────────────────────────┘
                          ↓ ONLY
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: libs/{vm,image,volume}/*.py - Components               │
│  ✅ Component wrapper: delegates to CRD or REST implementation   │
│  ✅ CRD implementation: makes actual kubectl/K8s API calls       │
│  ✅ REST implementation: makes actual REST API calls             │
│  ✅ Base: abstract base classes defining interface               │
└─────────────────────────────────────────────────────────────────┘
```

### Layer 1: Test Cases (.robot files)

**Purpose**: Define test scenarios and workflows
**Location**: `tests/regression/*.robot` or `tests/negative/*.robot`

```robot
*** Settings ***
Documentation    VM Basic Lifecycle Tests
...             This suite tests VM create, start, stop, and delete operations
Test Tags        regression    virtualmachines

Resource         ../../keywords/variables.resource
Resource         ../../keywords/common.resource
Resource         ../../keywords/virtualmachine.resource

Test Setup       Set Test Environment
Test Teardown    Cleanup Test Resources

*** Test Cases ***
Test VM Basic Lifecycle
    [Documentation]    Test complete VM lifecycle from creation to deletion
    ...               Steps:
    ...               1. Create a new VM with specified image
    ...               2. Start the VM
    ...               3. Verify VM reaches Running state
    ...               4. Stop the VM
    ...               5. Verify VM reaches Stopped state
    ...               6. Delete the VM
    ...               7. Verify VM no longer exists
    ...               Expected Result:
    ...               - All operations complete successfully
    ...               - VM transitions through expected states
    [Tags]    p0    coretest    smoke
    
    # Generate unique name to avoid conflicts
    ${vm_name}=    Generate Unique Name    test-vm
    
    # Call Layer 2 keywords ONLY
    Create VM    ${vm_name}    ${DEFAULT_IMAGE}    cpu=2    memory=4Gi
    Start VM    ${vm_name}
    Wait For VM Running    ${vm_name}    timeout=${WAIT_TIMEOUT}
    
    Stop VM    ${vm_name}
    Wait For VM Stopped    ${vm_name}    timeout=${WAIT_TIMEOUT}
    
    Delete VM    ${vm_name}
    Verify VM Not Exists    ${vm_name}
```

**Layer 1 Best Practices**:

1. **Imports**:
   ```robot
   # ✅ CORRECT - Import Layer 2 resource files
   Resource         ../../keywords/virtualmachine.resource
   Resource         ../../keywords/variables.resource
   
   # ❌ WRONG - Never import Python libraries directly
   Library          ../libs/vm/vm.py              # FORBIDDEN
   Library          ../libs/keywords/vm_keywords.py  # FORBIDDEN
   ```

2. **Keyword Calls**:
   ```robot
   # ✅ CORRECT - Call Layer 2 keywords
   Create VM    ${vm_name}    ${image}
   Start VM    ${vm_name}
   
   # ❌ WRONG - Never call Layer 3 or Layer 4 functions
   create_vm    ${vm_name}    ${image}    # FORBIDDEN (Layer 3)
   ```

3. **Documentation**:
   - Use `[Documentation]` with multi-line continuation `...`
   - Include Steps and Expected Result sections
   - Be specific about what the test validates

4. **Tags**:
   - **Priority**: `p0`, `p1`, `p2`, `p3`
   - **Category**: `coretest`, `regression`, `negative`, `sanity`, `smoke`
   - **Component**: `virtualmachines`, `images`, `volumes`, `networks`, `backup`, `ha`
   - **Speed**: `slow` for long-running tests

### Layer 2: Keyword Definitions (.resource files)

**Purpose**: Define reusable keywords that orchestrate test logic
**Location**: `keywords/*.resource`

```robot
*** Settings ***
Documentation    VM Keywords - Reusable keywords for VM operations
Library          ../libs/keywords/vm_keywords.py

*** Keywords ***
Create VM
    [Arguments]    ${vm_name}    ${image_name}    ${cpu}=2    ${memory}=4Gi
    [Documentation]    Create a new virtual machine
    ...               Args:
    ...                   vm_name: Name of the VM to create
    ...                   image_name: Image to use for the VM
    ...                   cpu: Number of CPU cores (default: 2)
    ...                   memory: Memory size (default: 4Gi)
    Log    Creating VM: ${vm_name} with image: ${image_name}
    
    # Call Layer 3 keyword wrapper function
    ${result}=    create_vm    ${vm_name}    ${image_name}    ${cpu}    ${memory}
    Should Be Equal    ${result}    success
    Log    VM ${vm_name} created successfully
    [Return]    ${vm_name}

Start VM
    [Arguments]    ${vm_name}
    [Documentation]    Start a virtual machine
    Log    Starting VM: ${vm_name}
    
    # Call Layer 3 keyword wrapper function
    start_vm    ${vm_name}
    Log    VM ${vm_name} start command issued

Wait For VM Running
    [Arguments]    ${vm_name}    ${timeout}=${WAIT_TIMEOUT}
    [Documentation]    Wait until VM reaches Running state
    ...               Args:
    ...                   vm_name: Name of the VM
    ...                   timeout: Maximum time to wait (default: WAIT_TIMEOUT)
    Log    Waiting for VM ${vm_name} to reach Running state
    
    # Use Robot Framework's Wait Until Keyword Succeeds
    Wait Until Keyword Succeeds
    ...    ${timeout}
    ...    10s
    ...    verify_vm_running    ${vm_name}
    
    Log    VM ${vm_name} is now Running

Delete VM
    [Arguments]    ${vm_name}
    [Documentation]    Delete a virtual machine
    Log    Deleting VM: ${vm_name}
    
    # Call Layer 3 keyword wrapper function
    delete_vm    ${vm_name}
    Log    VM ${vm_name} deleted

Verify VM Not Exists
    [Arguments]    ${vm_name}
    [Documentation]    Verify that VM no longer exists
    Log    Verifying VM ${vm_name} does not exist
    
    # Call Layer 3 keyword wrapper function
    ${exists}=    vm_exists    ${vm_name}
    Should Be Equal    ${exists}    ${False}
    Log    Confirmed: VM ${vm_name} does not exist
```

**Layer 2 Best Practices**:

1. **Imports**:
   ```robot
   # ✅ CORRECT - Import Layer 3 Python keyword libraries
   Library          ../libs/keywords/vm_keywords.py
   Library          ../libs/keywords/image_keywords.py
   
   # ❌ WRONG - Never import Layer 4 component files
   Library          ../libs/vm/vm.py         # FORBIDDEN
   Library          ../libs/vm/crd.py        # FORBIDDEN
   ```

2. **Function Calls**:
   ```robot
   # ✅ CORRECT - Call Layer 3 functions
   ${result}=    create_vm    ${name}    ${image}
   start_vm    ${name}
   
   # ❌ WRONG - Never call Layer 4 methods or make API calls
   # No kubectl, no REST calls, no kubernetes client
   ```

3. **Keyword Structure**:
   - Use `[Arguments]` for parameters with defaults
   - Use `[Documentation]` to describe purpose and arguments
   - Add logging for test visibility
   - Return values when needed with `[Return]`

4. **Error Handling**:
   - Use `Should Be Equal`, `Should Contain` for assertions
   - Let exceptions from Layer 3 bubble up naturally

### Layer 3: Keyword Wrappers (Python)

**Purpose**: Create component instances and delegate to Layer 4
**Location**: `libs/keywords/*_keywords.py`

```python
"""
VM Keywords for Robot Framework
Layer 3: Keyword wrappers - delegates to Layer 4 components

CRITICAL: This layer NEVER makes API calls directly.
All operations are delegated to Layer 4 components.
"""

from libs.vm.vm import VM
from libs.utility.utility import get_strategy


class VMKeywords:
    """
    VM keyword library for Robot Framework tests
    
    This class provides keyword methods that Robot Framework can call.
    All actual operations are delegated to Layer 4 VM component.
    """
    
    def __init__(self):
        """
        Initialize with Layer 4 component
        
        Creates a VM component instance based on the configured strategy
        (CRD or REST, determined by HARVESTER_OPERATION_STRATEGY env var)
        """
        # Get strategy from environment (crd or rest)
        strategy = get_strategy()
        
        # Create Layer 4 component instance
        self.vm = VM(strategy=strategy)
    
    def create_vm(self, vm_name, image_name, cpu=2, memory="4Gi"):
        """
        Create a new virtual machine
        
        Args:
            vm_name: Name of the VM to create
            image_name: Image to use for the VM
            cpu: Number of CPU cores (default: 2)
            memory: Memory size (default: 4Gi)
            
        Returns:
            str: "success" if VM was created successfully
            
        Raises:
            Exception: If VM creation fails
        """
        # Delegate to Layer 4 component - NO direct API calls here!
        self.vm.create(
            name=vm_name,
            image=image_name,
            cpu=int(cpu),
            memory=memory
        )
        return "success"
    
    def start_vm(self, vm_name):
        """
        Start a virtual machine
        
        Args:
            vm_name: Name of the VM to start
            
        Raises:
            Exception: If VM start fails
        """
        # Delegate to Layer 4 component
        self.vm.start(vm_name)
    
    def stop_vm(self, vm_name):
        """
        Stop a virtual machine
        
        Args:
            vm_name: Name of the VM to stop
            
        Raises:
            Exception: If VM stop fails
        """
        # Delegate to Layer 4 component
        self.vm.stop(vm_name)
    
    def verify_vm_running(self, vm_name):
        """
        Verify VM is in Running state
        
        Args:
            vm_name: Name of the VM to check
            
        Returns:
            bool: True if VM is running
            
        Raises:
            AssertionError: If VM is not in Running state
        """
        # Delegate to Layer 4 component
        status = self.vm.get_status(vm_name)
        
        if status != "Running":
            raise AssertionError(
                f"VM {vm_name} is not running. Current status: {status}"
            )
        return True
    
    def vm_exists(self, vm_name):
        """
        Check if VM exists
        
        Args:
            vm_name: Name of the VM to check
            
        Returns:
            bool: True if VM exists, False otherwise
        """
        # Delegate to Layer 4 component
        return self.vm.exists(vm_name)
    
    def delete_vm(self, vm_name):
        """
        Delete a virtual machine
        
        Args:
            vm_name: Name of the VM to delete
            
        Raises:
            Exception: If VM deletion fails
        """
        # Delegate to Layer 4 component
        self.vm.delete(vm_name)
    
    def get_vm_ip(self, vm_name):
        """
        Get VM IP address
        
        Args:
            vm_name: Name of the VM
            
        Returns:
            str: IP address of the VM
            
        Raises:
            Exception: If IP cannot be retrieved
        """
        # Delegate to Layer 4 component
        return self.vm.get_ip(vm_name)
```

**Layer 3 Critical Rules**:

1. **Imports**:
   ```python
   # ✅ CORRECT - Import Layer 4 components
   from libs.vm.vm import VM
   from libs.image.image import Image
   from libs.utility.utility import get_strategy
   
   # ❌ WRONG - Never import API libraries
   import requests                    # FORBIDDEN
   from kubernetes import client      # FORBIDDEN
   import subprocess                  # FORBIDDEN (for kubectl)
   ```

2. **Component Usage**:
   ```python
   # ✅ CORRECT - Create and use Layer 4 components
   def __init__(self):
       self.vm = VM(strategy=get_strategy())
   
   def create_vm(self, name, image):
       self.vm.create(name, image)  # Delegate to Layer 4
   
   # ❌ WRONG - Never make direct API calls
   def create_vm(self, name, image):
       requests.post(...)           # FORBIDDEN
       subprocess.run(['kubectl'...])  # FORBIDDEN
   ```

3. **Method Design**:
   - Methods should match Robot Framework keyword naming (snake_case)
   - Provide clear docstrings with Args, Returns, Raises
   - Handle only Robot Framework integration logic
   - Let Layer 4 handle all API operations

### Layer 4: Components (Python)

**Purpose**: Actual API implementation (CRD and REST)
**Location**: `libs/{vm,image,volume,host}/*.py`

**File Structure per Component**:
- `base.py` - Abstract base class defining interface
- `crd.py` - CRD/Kubernetes implementation
- `rest.py` - REST API implementation  
- `{component}.py` - Component wrapper selecting implementation

**Example: libs/vm/base.py (Abstract Base)**

```python
"""
VM Base - Abstract interface for VM operations
Layer 4: Defines the contract that all implementations must follow
"""

from abc import ABC, abstractmethod


class VMBase(ABC):
    """
    Abstract base class for VM operations
    
    All VM implementations (CRD, REST) must inherit from this class
    and implement all abstract methods.
    """
    
    @abstractmethod
    def create(self, name, image, cpu, memory, **kwargs):
        """
        Create a virtual machine
        
        Args:
            name: VM name
            image: Image name to use
            cpu: Number of CPU cores
            memory: Memory size (e.g., "4Gi")
            **kwargs: Additional VM configuration
        """
        pass
    
    @abstractmethod
    def start(self, name):
        """Start a virtual machine"""
        pass
    
    @abstractmethod
    def stop(self, name):
        """Stop a virtual machine"""
        pass
    
    @abstractmethod
    def get_status(self, name):
        """
        Get VM status
        
        Returns:
            str: Status like "Running", "Stopped", "Starting", etc.
        """
        pass
    
    @abstractmethod
    def exists(self, name):
        """
        Check if VM exists
        
        Returns:
            bool: True if VM exists
        """
        pass
    
    @abstractmethod
    def delete(self, name):
        """Delete a virtual machine"""
        pass
    
    @abstractmethod
    def get_ip(self, name):
        """
        Get VM IP address
        
        Returns:
            str: IP address
        """
        pass
```

**Example: libs/vm/crd.py (CRD Implementation)**

```python
"""
VM CRD Implementation - Kubernetes API operations
Layer 4: Makes actual kubectl/K8s API calls
"""

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from libs.vm.base import VMBase


class VMCRD(VMBase):
    """
    CRD implementation for VM operations using Kubernetes API
    
    This implementation:
    - Uses kubernetes Python client
    - Works with KubeVirt VirtualMachine CRDs
    - Requires KUBECONFIG to be configured
    """
    
    def __init__(self):
        """Initialize Kubernetes client"""
        # Load kubeconfig from default location or KUBECONFIG env var
        config.load_kube_config()
        
        # Create custom objects API client for CRDs
        self.custom_api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        
        # KubeVirt VM CRD details
        self.group = "kubevirt.io"
        self.version = "v1"
        self.plural = "virtualmachines"
        self.namespace = "default"
    
    def create(self, name, image, cpu=2, memory="4Gi", **kwargs):
        """
        Create VM using Kubernetes CRD
        
        Creates a KubeVirt VirtualMachine custom resource
        """
        vm_manifest = {
            "apiVersion": f"{self.group}/{self.version}",
            "kind": "VirtualMachine",
            "metadata": {
                "name": name,
                "namespace": self.namespace
            },
            "spec": {
                "running": False,  # Don't start automatically
                "template": {
                    "metadata": {
                        "labels": {"kubevirt.io/vm": name}
                    },
                    "spec": {
                        "domain": {
                            "cpu": {"cores": int(cpu)},
                            "memory": {"guest": memory},
                            "devices": {
                                "disks": [
                                    {
                                        "name": "rootdisk",
                                        "disk": {"bus": "virtio"}
                                    }
                                ]
                            }
                        },
                        "volumes": [
                            {
                                "name": "rootdisk",
                                "dataVolume": {
                                    "name": image
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        try:
            self.custom_api.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                body=vm_manifest
            )
        except ApiException as e:
            raise Exception(f"Failed to create VM {name}: {e}")
    
    def start(self, name):
        """Start VM by patching spec.running to true"""
        patch = {"spec": {"running": True}}
        
        try:
            self.custom_api.patch_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name,
                body=patch
            )
        except ApiException as e:
            raise Exception(f"Failed to start VM {name}: {e}")
    
    def stop(self, name):
        """Stop VM by patching spec.running to false"""
        patch = {"spec": {"running": False}}
        
        try:
            self.custom_api.patch_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name,
                body=patch
            )
        except ApiException as e:
            raise Exception(f"Failed to stop VM {name}: {e}")
    
    def get_status(self, name):
        """Get VM status from CRD"""
        try:
            vm = self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name
            )
            return vm.get("status", {}).get("printableStatus", "Unknown")
        except ApiException as e:
            if e.status == 404:
                raise Exception(f"VM {name} not found")
            raise Exception(f"Failed to get VM {name} status: {e}")
    
    def exists(self, name):
        """Check if VM exists"""
        try:
            self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name
            )
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise Exception(f"Failed to check if VM {name} exists: {e}")
    
    def delete(self, name):
        """Delete VM CRD"""
        try:
            self.custom_api.delete_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name
            )
        except ApiException as e:
            if e.status == 404:
                # Already deleted
                return
            raise Exception(f"Failed to delete VM {name}: {e}")
    
    def get_ip(self, name):
        """Get VM IP from VMI (VirtualMachineInstance)"""
        try:
            vmi = self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural="virtualmachineinstances",
                name=name
            )
            interfaces = vmi.get("status", {}).get("interfaces", [])
            if interfaces and len(interfaces) > 0:
                return interfaces[0].get("ipAddress")
            return None
        except ApiException as e:
            raise Exception(f"Failed to get IP for VM {name}: {e}")
```

**Example: libs/vm/rest.py (REST Implementation)**

```python
"""
VM REST Implementation - Harvester REST API operations
Layer 4: Makes actual REST API calls
"""

import os
import requests
from libs.vm.base import VMBase


class VMRest(VMBase):
    """
    REST implementation for VM operations using Harvester API
    
    This implementation:
    - Uses Harvester REST API endpoints
    - Requires HARVESTER_ENDPOINT, HARVESTER_USERNAME, HARVESTER_PASSWORD
    - Suitable for remote testing without direct cluster access
    """
    
    def __init__(self):
        """Initialize REST client and authenticate"""
        self.endpoint = os.getenv("HARVESTER_ENDPOINT")
        self.username = os.getenv("HARVESTER_USERNAME", "admin")
        self.password = os.getenv("HARVESTER_PASSWORD")
        
        if not self.endpoint or not self.password:
            raise ValueError(
                "HARVESTER_ENDPOINT and HARVESTER_PASSWORD must be set"
            )
        
        self.session = requests.Session()
        self.session.verify = False  # For self-signed certs
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Harvester API"""
        auth_url = f"{self.endpoint}/v3-public/localProviders/local"
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        response = self.session.post(auth_url, json=payload)
        response.raise_for_status()
        
        # Extract token from response
        token = response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def create(self, name, image, cpu=2, memory="4Gi", **kwargs):
        """Create VM using REST API"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines"
        
        payload = {
            "type": "kubevirt.io.virtualmachine",
            "metadata": {"name": name, "namespace": "default"},
            "spec": {
                "running": False,
                "template": {
                    "spec": {
                        "domain": {
                            "cpu": {"cores": cpu},
                            "memory": {"guest": memory}
                        },
                        "volumes": [
                            {"name": "rootdisk", "dataVolume": {"name": image}}
                        ]
                    }
                }
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
    
    def start(self, name):
        """Start VM using REST API"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines/default/{name}"
        
        # Get current VM state
        response = self.session.get(url)
        response.raise_for_status()
        vm_data = response.json()
        
        # Update running state
        vm_data["spec"]["running"] = True
        
        response = self.session.put(url, json=vm_data)
        response.raise_for_status()
    
    def stop(self, name):
        """Stop VM using REST API"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines/default/{name}"
        
        response = self.session.get(url)
        response.raise_for_status()
        vm_data = response.json()
        
        vm_data["spec"]["running"] = False
        
        response = self.session.put(url, json=vm_data)
        response.raise_for_status()
    
    def get_status(self, name):
        """Get VM status"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines/default/{name}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        vm_data = response.json()
        return vm_data.get("status", {}).get("printableStatus", "Unknown")
    
    def exists(self, name):
        """Check if VM exists"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines/default/{name}"
        
        response = self.session.get(url)
        return response.status_code == 200
    
    def delete(self, name):
        """Delete VM"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachines/default/{name}"
        
        response = self.session.delete(url)
        if response.status_code not in [200, 204, 404]:
            response.raise_for_status()
    
    def get_ip(self, name):
        """Get VM IP address"""
        url = f"{self.endpoint}/v1/harvester/kubevirt.io.virtualmachineinstances/default/{name}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        vmi_data = response.json()
        interfaces = vmi_data.get("status", {}).get("interfaces", [])
        if interfaces:
            return interfaces[0].get("ipAddress")
        return None
```

**Example: libs/vm/vm.py (Component Wrapper)**

```python
"""
VM Component - Layer 4 wrapper
Selects and delegates to CRD or REST implementation
"""

from libs.vm.base import VMBase
from libs.vm.crd import VMCRD
from libs.vm.rest import VMRest


class VM:
    """
    VM component that delegates to CRD or REST implementation
    
    The implementation is selected based on:
    - HARVESTER_OPERATION_STRATEGY environment variable
    - Defaults to 'crd' if not set
    
    Usage:
        vm = VM(strategy='crd')  # Use CRD implementation
        vm = VM(strategy='rest') # Use REST implementation
    """
    
    def __init__(self, strategy='crd'):
        """
        Initialize VM component
        
        Args:
            strategy: 'crd' or 'rest' (default: 'crd')
            
        Raises:
            ValueError: If strategy is not 'crd' or 'rest'
        """
        if strategy == 'crd':
            self._impl = VMCRD()
        elif strategy == 'rest':
            self._impl = VMRest()
        else:
            raise ValueError(
                f"Unknown strategy: {strategy}. Must be 'crd' or 'rest'"
            )
        
        self.strategy = strategy
    
    def create(self, name, image, cpu=2, memory="4Gi", **kwargs):
        """Create a VM - delegates to implementation"""
        return self._impl.create(name, image, cpu, memory, **kwargs)
    
    def start(self, name):
        """Start a VM - delegates to implementation"""
        return self._impl.start(name)
    
    def stop(self, name):
        """Stop a VM - delegates to implementation"""
        return self._impl.stop(name)
    
    def get_status(self, name):
        """Get VM status - delegates to implementation"""
        return self._impl.get_status(name)
    
    def exists(self, name):
        """Check if VM exists - delegates to implementation"""
        return self._impl.exists(name)
    
    def delete(self, name):
        """Delete a VM - delegates to implementation"""
        return self._impl.delete(name)
    
    def get_ip(self, name):
        """Get VM IP - delegates to implementation"""
        return self._impl.get_ip(name)
```

**Layer 4 Best Practices**:

1. **Abstract Base Class**: Always define interface in `base.py`
2. **Separate Implementations**: Keep CRD and REST logic completely separate
3. **Component Wrapper**: Use wrapper to select implementation
4. **Error Handling**: Provide clear error messages
5. **Consistency**: Both implementations should behave identically
6. **Documentation**: Document API-specific quirks

### Robot Framework Variables

Use centralized variables from `keywords/variables.resource`:

```robot
*** Variables ***
# Wait timeouts
${WAIT_TIMEOUT}          %{WAIT_TIMEOUT=600}
${SHORT_TIMEOUT}         %{SHORT_TIMEOUT=60}

# Image configuration
${DEFAULT_IMAGE}         %{DEFAULT_IMAGE=opensuse-leap}

# Network configuration
${VLAN_ID}               %{VLAN_ID=100}
${VLAN_NIC}              %{VLAN_NIC=mgmt}

# Strategy
${OPERATION_STRATEGY}    %{HARVESTER_OPERATION_STRATEGY=crd}
```

Variables use `%{ENV_VAR=default}` syntax to read from environment with fallback defaults.

### Robot Framework Assertions and Patterns

```robot
# Equality checks
Should Be Equal              ${actual}    ${expected}
Should Be Equal As Numbers   ${num1}      ${num2}
Should Not Be Equal          ${actual}    ${unexpected}

# String checks
Should Contain               ${text}      ${substring}
Should Start With            ${text}      ${prefix}
Should Match Regexp          ${text}      ${pattern}

# Boolean checks
Should Be True               ${condition}
Should Be Empty              ${variable}
Should Not Be Empty          ${variable}

# Wait patterns
Wait Until Keyword Succeeds
    ...    ${TIMEOUT}
    ...    10s
    ...    Verification Keyword    ${args}

# Error handling
Run Keyword And Expect Error    Expected error message    Failing Keyword
Run Keyword And Ignore Error    Might Fail Keyword
```

### Strategy Configuration

Set the operational strategy via environment variable:

```bash
# CRD Strategy (default) - requires KUBECONFIG
export HARVESTER_OPERATION_STRATEGY=crd
export KUBECONFIG=$HOME/.kube/config

# REST Strategy - requires Harvester credentials
export HARVESTER_OPERATION_STRATEGY=rest
export HARVESTER_ENDPOINT=https://harvester-vip
export HARVESTER_USERNAME=admin
export HARVESTER_PASSWORD=password
```

### Common Violations to Avoid

❌ **NEVER do this**:
```robot
# Layer 1 importing Layer 3 or 4
Library    ../libs/keywords/vm_keywords.py    # WRONG
Library    ../libs/vm/vm.py                   # WRONG

# Layer 2 importing Layer 4
Library    ../libs/vm/crd.py                  # WRONG
```

❌ **NEVER do this**:
```python
# Layer 3 making API calls
class VMKeywords:
    def create_vm(self, name):
        requests.post(...)        # WRONG
        subprocess.run(['kubectl'...])  # WRONG
```

✅ **ALWAYS do this**:
```robot
# Layer 1 imports Layer 2
Resource    ../../keywords/virtualmachine.resource  # CORRECT
```

```robot
# Layer 2 imports Layer 3
Library    ../libs/keywords/vm_keywords.py  # CORRECT
```

```python
# Layer 3 uses Layer 4
from libs.vm.vm import VM  # CORRECT

class VMKeywords:
    def __init__(self):
        self.vm = VM(strategy=get_strategy())
    
    def create_vm(self, name, image):
        self.vm.create(name, image)  # Delegate to Layer 4
```

## 3. Advanced Fixture Patterns

### Using Checker Fixtures

Many common verification patterns are available through checker fixtures. These fixtures provide reusable methods for waiting and verifying resource states:

```python
# Volume checker fixture
@pytest.fixture(scope="session")
def volume_checker(api_client, wait_timeout, sleep_timeout):
    class VolumeChecker:
        def __init__(self):
            self.volumes = api_client.volumes
            self.lhvolumes = api_client.lhvolumes
        
        @wait_until(wait_timeout, sleep_timeout)
        def wait_volumes_detached(self, vol_names):
            for vol_name in vol_names:
                code, data = self.volumes.get(name=vol_name)
                if not (code == 200):
                    return False, (code, data)
                # Additional verification logic
            return True, (code, data)
    
    return VolumeChecker()

# VM checker fixture
@pytest.fixture(scope="session")
def vm_checker(api_client, wait_timeout, sleep_timeout, vm_shell):
    from dataclasses import dataclass, field
    
    @dataclass
    class ResponseContext:
        callee: str
        code: int
        data: dict
        options: dict = field(default_factory=dict, compare=False)
        
        def __iter__(self):
            '''Handy method to be used for unpacking'''
            return iter([self.code, self.data])
    
    class VMChecker:
        def __init__(self, vms_api, timeout, sleep_time):
            self.vms = vms_api
            self.timeout = timeout
            self.sleep = sleep_time
        
        # Add checker methods here
    
    return VMChecker(api_client.vms, wait_timeout, sleep_timeout)
```

### Nested Classes and Functions in Fixtures

Fixtures can use nested classes and functions to provide organized helper functionality:

```python
@pytest.fixture(scope="session")
def host_shell(request):
    """Provides SSH shell access to hosts"""
    
    class HostShell:
        _client = _jump = None
        
        def __init__(self, username, password=None, pkey=None):
            self.username = username
            self.password = password
            self.pkey = pkey
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, exc_tb):
            self.logout()
        
        def login(self, ipaddr, port=22, jumphost=False, **kwargs):
            if not self.client:
                cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                # Connection setup
                self._client = cli
            return self
        
        def logout(self):
            if self.client and self.client.get_transport():
                self.client.close()
                self._client = None
        
        def exec_command(self, command, **kwargs):
            _, out, err = self.client.exec_command(command, **kwargs)
            return out.read().decode(), err.read().decode()
    
    # Return configured instance
    username = request.config.getoption("--host-username")
    password = request.config.getoption("--host-password")
    return HostShell(username, password)
```

### Polling and Waiting Utilities

Use the `polling_for` fixture for complex polling scenarios:

```python
@pytest.fixture(scope="session")
def polling_for(wait_timeout, sleep_timeout):
    def _polling_for(subject: str, checker: Callable[..., bool], 
                     poller: Callable, *args, timeout=wait_timeout):
        """
        Polling expected condition for `timeout`s every `sleep_timeout`s
        
        Arguments:
            subject: str, what is waiting for
            checker: Callable, check `poller` output and returns bool
            args: list, [*poller_args, testee]
            poller: Callable, poller(*poller_args, testee) for each testee
        
        Returns:
            Any: `poller` output if qualified by `checker`
        
        Raises:
            AssertionError: if still NOT qualified within `timeout`s
        """
        *poller_args, testee = args
        testees = testee if isinstance(testee, list) else [testee]
        
        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            for testee in testees[:]:
                output = poller(*poller_args, testee)
                qualified = checker(*output)
                if qualified:
                    testees.remove(testee)
            if not testees:
                return output
            sleep(sleep_timeout)
        else:
            raise AssertionError(
                f'Timeout {timeout}s waiting for {subject}\n'
                f'Got error: {output}'
            )
    
    return _polling_for

# Usage example
def test_resources_ready(api_client, polling_for):
    def check_ready(code, data):
        return code == 200 and data.get('status') == 'ready'
    
    def get_resource(name):
        return api_client.resources.get(name)
    
    polling_for(
        "resources to be ready",
        check_ready,
        get_resource,
        ["resource-1", "resource-2", "resource-3"]
    )
```

### Dataclass Patterns for Test Data

Use dataclasses for structured test data and contexts:

```python
from dataclasses import dataclass, field

@dataclass
class ResponseContext:
    """Context for API responses"""
    callee: str
    code: int
    data: dict
    options: dict = field(default_factory=dict, compare=False)
    
    def __iter__(self):
        '''Handy method to unpack response'''
        return iter([self.code, self.data])

@dataclass
class ShellContext:
    """Context for shell command execution"""
    command: str
    stdout: str
    stderr: str
    options: dict = field(default_factory=dict, compare=False)
    
    def __iter__(self):
        return iter([self.stdout, self.stderr])

# Usage in tests
def test_with_context(api_client):
    ctx = ResponseContext(
        callee="create_vm",
        code=201,
        data={"name": "test-vm"},
        options={"validate": True}
    )
    
    # Can unpack easily
    code, data = ctx
    assert code == 201
```

### Naming Conventions for Test Methods

- **Test methods**: Use descriptive names without underscore prefixes (e.g., `test_create_vm`, not `_test_create_vm`)
- **Fixture helper methods**: Can use underscores when part of a fixture class structure (e.g., nested methods in checker fixtures)
- **Private fixture methods**: Use single underscore for internal fixture methods not meant for direct test use

Example:
```python
class TestVMLifecycle:
    # Good - standard test method
    def test_create_vm(self, api_client):
        pass
    
    # Good - test method with clear action
    def test_verify_vm_running(self, api_client):
        pass

# Fixture with nested functionality
@pytest.fixture(scope="session")
def vm_checker(api_client):
    class VMChecker:
        def wait_for_running(self, vm_name):
            # Public method for tests
            pass
        
        def _internal_check(self, status):
            # Private helper method within fixture
            pass
    
    return VMChecker()
```

## 4. Migrating Tests from Pytest to Robot Framework

### Migration Strategy

#### Step 1: Analyze Pytest Test

```python
# Original pytest test
@pytest.mark.p0
class TestFeature:
    def test_create_resource(self, api_client):
        """Create a resource"""
        code, data = api_client.resources.create("test-resource")
        assert code == 201
```

#### Step 2: Create Robot Framework Equivalent

```robot
*** Test Cases ***
Test Create Resource
    [Documentation]    Create a resource
    [Tags]    p0
    
    ${code}    ${data}=    Create Resource    test-resource
    Should Be Equal As Numbers    ${code}    201
```

#### Step 3: Migration Checklist

- [ ] Convert test class to Test Cases section
- [ ] Convert pytest markers to Robot tags
- [ ] Convert fixtures to Keywords or Library calls
- [ ] Convert assertions to Robot assertions
- [ ] Convert docstrings to Documentation
- [ ] Convert setup/teardown to Robot Setup/Teardown
- [ ] Migrate any custom utilities to Robot keywords

### Migration Patterns

#### 1. Test Class → Test Suite
```python
# Pytest
@pytest.mark.p0
@pytest.mark.addons
class TestVMDHCPControllerAddon:
    """Test VM DHCP Controller Addon functionality"""
```

```robot
# Robot
*** Settings ***
Documentation    Test VM DHCP Controller Addon functionality
Default Tags     p0    addons
```

#### 2. Test Method → Test Case
```python
# Pytest
@pytest.mark.dependency(name="setup")
def test_setup_addon(self, api_client, wait_timeout):
    """Setup the addon"""
    code, data = api_client.addons.enable(addon_id)
    assert code == 200
```

```robot
# Robot
*** Test Cases ***
Test Setup Addon
    [Documentation]    Setup the addon
    [Tags]    setup
    
    ${code}    ${data}=    Enable Addon    ${ADDON_ID}
    Should Be Equal As Numbers    ${code}    200
```

#### 3. Fixtures → Keywords/Libraries
```python
# Pytest fixture usage
def test_something(self, api_client, unique_name):
    resource_name = f"test-{unique_name}"
```

```robot
# Robot keyword
*** Keywords ***
Get Unique Resource Name
    [Arguments]    ${prefix}
    ${timestamp}=    Get Time    epoch
    ${name}=    Set Variable    ${prefix}-${timestamp}
    [Return]    ${name}

*** Test Cases ***
Test Something
    ${resource_name}=    Get Unique Resource Name    test
```

#### 4. Assertions → Robot Assertions
```python
# Pytest
assert code == 200, f"Expected 200, got {code}"
assert "Running" in status
assert vm_ip is not None
```

```robot
# Robot
Should Be Equal As Numbers    ${code}    200    Expected 200, got ${code}
Should Contain    ${status}    Running
Should Not Be Empty    ${vm_ip}
```

#### 5. Wait Loops → Wait Until Keyword Succeeds
```python
# Pytest
endtime = datetime.now() + timedelta(seconds=wait_timeout)
while endtime > datetime.now():
    code, data = api_client.vms.get_status(vm_name)
    if data.get('status') == 'Running':
        break
    sleep(5)
else:
    raise AssertionError("VM did not start")
```

```robot
# Robot
Wait Until Keyword Succeeds
    ...    ${TIMEOUT}
    ...    5s
    ...    VM Should Be Running    ${vm_name}

*** Keywords ***
VM Should Be Running
    [Arguments]    ${vm_name}
    ${code}    ${data}=    Get VM Status    ${vm_name}
    Should Be Equal    ${data}[status]    Running
```

#### 6. Exception Handling → Run Keyword And Ignore Error
```python
# Pytest
try:
    api_client.resources.delete(resource_name)
except Exception as e:
    print(f"Cleanup failed: {e}")
```

```robot
# Robot
Run Keyword And Ignore Error    Delete Resource    ${resource_name}

# Or with logging
${status}    ${result}=    Run Keyword And Ignore Error    Delete Resource    ${resource_name}
Run Keyword If    '${status}' == 'FAIL'    Log    Cleanup failed: ${result}    WARN
```

### Migration Best Practices

1. **Keep Test Logic Identical**: Ensure migrated tests verify the same functionality
2. **Maintain Documentation**: Preserve all docstrings and comments
3. **Preserve Tags**: Convert pytest markers to equivalent Robot tags
4. **Test Dependencies**: Use `[Depends On]` or separate suites for dependencies
5. **Reuse Keywords**: Create reusable keywords for common operations
6. **Error Messages**: Preserve informative error messages
7. **Cleanup**: Ensure cleanup logic is maintained in teardown

### Common Pitfalls to Avoid

1. ❌ Don't lose test coverage during migration
2. ❌ Don't skip documentation
3. ❌ Don't forget cleanup in teardown
4. ❌ Don't ignore test dependencies
5. ❌ Don't create overly complex keywords
6. ✅ Do test the migrated code
7. ✅ Do maintain consistent naming
8. ✅ Do preserve all assertions

## General Guidelines for All Test Development

### Code Quality Standards

1. **Linting**: All Python code must pass flake8
   ```bash
   flake8 harvester_e2e_tests/
   ```

2. **Line Length**: Maximum 99 characters per line

3. **Documentation**: Every test must have clear documentation

4. **Naming Conventions**:
   - Pytest: `test_<action>_<feature>`
   - Robot: `Test <Action> <Feature>`
   - Classes: `Test<FeatureName>`
   - Keywords: `<Verb> <Object>`

5. **Error Handling**: Always handle cleanup even on failure

6. **Security**: Use `# nosec B607` for subprocess calls where appropriate

### Testing Best Practices

1. **Test Independence**: Each test should be runnable independently
2. **Cleanup**: Always clean up resources in finally blocks or teardown
3. **Timeouts**: Use appropriate timeouts, default to fixture value
4. **Assertions**: Include meaningful error messages
5. **Idempotency**: Tests should be idempotent where possible
6. **Skip Appropriately**: Use `pytest.skip()` or `Skip If` for missing prerequisites

### Resource Naming Convention

```python
# Pytest
resource_name = f"{feature}-test-{unique_name}"
```

```robot
# Robot
${RESOURCE_NAME}=    Set Variable    ${FEATURE}-test-${UNIQUE_NAME}
```

### Common Test Patterns

#### Create-Verify-Delete Pattern
```python
# Pytest
try:
    # Create
    code, data = api_client.resource.create(name)
    assert code == 201
    
    # Verify
    code, data = api_client.resource.get(name)
    assert code == 200
    assert data['status'] == 'ready'
finally:
    # Delete
    api_client.resource.delete(name)
```

```robot
# Robot
*** Test Cases ***
Test Resource Lifecycle
    ${name}=    Create Test Resource
    Verify Resource Ready    ${name}
    [Teardown]    Delete Test Resource    ${name}
```

#### Dependency Chain Pattern

Use pytest-dependency for test ordering:

```python
@pytest.mark.dependency(name="create_resource")
def test_create_resource(self, api_client, unique_name, resource_state):
    code, data = api_client.resources.create(unique_name)
    assert 201 == code, (code, data)
    resource_state.uid = data['metadata']['name']

@pytest.mark.dependency(name="get_resource", depends=["create_resource"])
def test_get_resource(self, api_client, resource_state):
    code, data = api_client.resources.get(resource_state.uid)
    assert 200 == code, (code, data)

@pytest.mark.dependency(depends=["get_resource"])
def test_delete_resource(self, api_client, resource_state):
    code, data = api_client.resources.delete(resource_state.uid)
    assert 200 == code, (code, data)
```

#### Module-scoped Fixture Pattern

For resources shared across a test class:

```python
@pytest.fixture(scope="module")
def shared_image(api_client, image_opensuse, unique_name, wait_timeout):
    """Create an image shared across all tests in module"""
    image_name = f"test-image-{unique_name}"
    code, data = api_client.images.create(image_name, image_opensuse.url)
    assert 201 == code, (code, data)
    
    # Wait for image to be ready
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(image_name)
        if code == 200 and data.get('status', {}).get('progress') == 100:
            break
        sleep(5)
    
    yield data
    
    # Teardown
    code, data = api_client.images.delete(image_name)

@pytest.fixture(scope="class")
def test_vm(api_client, shared_image, ssh_keypair, wait_timeout):
    """Create a VM for test class"""
    vm_name = f"test-vm-{datetime.now().strftime('%Hh%Mm%Ss')}"
    pub_key, priv_key = ssh_keypair
    
    code, data = api_client.vms.create(
        vm_name, 
        image=shared_image['metadata']['name'],
        ssh_key=pub_key
    )
    assert 201 == code, (code, data)
    
    yield data
    
    # Teardown
    code, data = api_client.vms.delete(vm_name)
```

#### Test State Management Pattern

Use a state object to share data between dependent tests:

```python
@pytest.fixture(scope="class")
def support_bundle_state():
    """State object for support bundle tests"""
    class SupportBundleState:
        def __init__(self):
            self.uid = ""
            self.files = []
    
    return SupportBundleState()

@pytest.mark.support_bundle
class TestSupportBundle:
    @pytest.mark.dependency(name="create_bundle")
    def test_create(self, api_client, unique_name, support_bundle_state):
        code, data = api_client.supportbundle.create(unique_name)
        assert 201 == code, (code, data)
        support_bundle_state.uid = data['metadata']['name']
    
    @pytest.mark.dependency(depends=["create_bundle"])
    def test_download(self, api_client, support_bundle_state, wait_timeout):
        # Wait for bundle to be ready
        wait_for_support_bundle_ready(
            api_client, 
            support_bundle_state.uid, 
            wait_timeout
        )
        
        # Download and store file list
        code, data = api_client.supportbundle.download(support_bundle_state.uid)
        assert 200 == code
        support_bundle_state.files = extract_file_list(data)
    
    @pytest.mark.dependency(depends=["create_bundle"])
    def test_verify_contents(self, support_bundle_state):
        # Use stored file list from previous test
        assert len(support_bundle_state.files) > 0
        # Verify specific files exist
        patterns = [r"^.*/logs/.*\.log", r"^.*/cluster-info/.*"]
        for pattern in patterns:
            assert any(re.match(pattern, f) for f in support_bundle_state.files)
```

#### Version-specific Test Pattern

Use skip_version_if fixture for version-specific tests:

```python
@pytest.mark.skip_version_if("< v1.6.0", reason="New feature in v1.6.0")
class TestNewFeature:
    def test_feature(self, api_client):
        # This test only runs on v1.6.0+
        pass

@pytest.mark.skip_version_before("v1.5.0", reason="Feature not available before v1.5.0")
def test_old_feature(api_client):
    # This test only runs on v1.5.0+
    pass

@pytest.mark.skip_version_after("v1.4.0", reason="Feature removed after v1.4.0")
def test_deprecated_feature(api_client):
    # This test only runs up to v1.4.0
    pass
```

#### SSH Keypair Pattern

Generate and use SSH keypairs for VM access:

```python
@pytest.fixture(scope="module")
def ssh_keypair():
    """Generate SSH keypair for tests"""
    from cryptography.hazmat.primitives import asymmetric, serialization
    from cryptography.hazmat.backends import default_backend
    
    private_key = asymmetric.rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend()
    )
    
    private_key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption()
    )
    
    public_key = private_key.public_key()
    public_key_ssh = public_key.public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )
    
    return public_key_ssh.decode('utf-8'), private_key_pem.decode('utf-8')
```

## Additional Resources

- **Pytest Documentation**: https://docs.pytest.org/
- **Robot Framework Documentation**: https://robotframework.org/robotframework/
- **Harvester Documentation**: https://docs.harvesterhci.io/
- **Repository**: https://github.com/harvester/tests
- **Harvester API Client**: See `apiclient/harvester_api/` for API usage patterns
- **Test Fixtures**: See `harvester_e2e_tests/fixtures/` for reusable fixtures

## Reference Examples

For concrete examples of these patterns in action:

- **Support Bundle Tests**: `harvester_e2e_tests/apis/test_support_bundle.py`
- **VM Tests**: `harvester_e2e_tests/integrations/test_3_vm_functions.py`
- **Host Tests**: `harvester_e2e_tests/apis/test_hosts.py`
- **Network Tests**: `harvester_e2e_tests/integrations/test_1_images.py`
- **Fixtures**: `harvester_e2e_tests/fixtures/virtualmachines.py`, `volumes.py`, `networks.py`
