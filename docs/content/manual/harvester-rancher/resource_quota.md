---
title: Rancher Resource quota management
---
Ref: https://github.com/harvester/harvester/issues/1450

## Verify Items
  - Project's Resource quotas can be updated correctly
  - **Namespace Default Limit** should be assigned as the Project configured
  - Namespace moving between projects should work correctly

## Case: Create Namespace with Resource quotas
1. Install Harvester with any nodes
1. Install Rancher
1. Login to Rancher, import Harvester from _Virtualization Management_
1. Access Harvester dashboard via _Virtualization Management_
1. Navigate to _Project/Namespaces_, Create Project `A` with Resource quotas
1. Create Namespace `N1` based on Project `A`
1. The Default value of Resource Quotas should be the same as **Namespace Default Limit** assigned in Project `A`
1. Modifying **resource limit** should work correctly (when increasing/decreasing, the value should increased/decreased)
1. After `N1` Created, Click **Edit Config** on `N1`
1. **resource limit** should be the same as we assigned
1. Increase/decrease **resource limit** then Save
1. Click **Edit Config** on `N1`, **resource limit** should be the same as we assigned
1. Click **Edit Config** on `N1`, then increase **resource limit** exceeds Project `A`'s Limit
1. Click **Save** Button, error message should shown.
1. Click **Edit Config** on `N1`, then change the **Project** to `Default`
1. The Namespace `N1` should be moved to Project `Default`
