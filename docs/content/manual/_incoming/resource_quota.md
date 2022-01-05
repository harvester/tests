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
2. Install Rancher
3. Login to Rancher, import Harvester from _Virtualization Management_
4. Access Harvester dashboard via _Virtualization Management_
5. Navigate to _Project/Namespaces_, Create Project `A` with Resource quotas
6. Create Namespace `N1` based on Project `A`
7. The Default value of Resource Quotas should be the same as **Namespace Default Limit** assigned in Project `A`
8. Modifying **resource limit** should work correctly (when increasing/decreasing, the value should increased/decreased)
9. After `N1` Created, Click **Edit Config** on `N1`
10. **resource limit** should be the same as we assigned
11. Increase/decrease **resource limit** then Save
12. Click **Edit Config** on `N1`, **resource limit** should be the same as we assigned
13. Click **Edit Config** on `N1`, then increase **resource limit** exceeds Project `A`'s Limit
14. Click **Save** Button, error message should shown.
15. Click **Edit Config** on `N1`, then change the **Project** to `Default`
16. The Namespace `N1` should be moved to Project `Default`
