---
title: RBAC Cluster Owner
---

* Related issues: [#2626](https://github.com/harvester/harvester/issues/2626) [BUG] Access Harvester project/namespace page hangs with no response timeout with local owner role from Rancher

## Category: 
* Authentication

## Verification Steps
1. Import Harvester from Rancher
1. Create a standard user local in Rancher User & Authentication
1. Open Cluster Management page
1. Edit cluster config
![image](https://user-images.githubusercontent.com/29251855/182781682-5cdd3c6a-517b-4f61-980d-3ee3cab86745.png)
1. Expand Member Roles
1. Add local user with Cluster Owner role
![image](https://user-images.githubusercontent.com/29251855/182781823-b71ba504-6488-4581-b50d-17c333496b8c.png)
1. Logout Admin
1. Login with local user
1. Access Harvester from virtualization management
1. Click the Project/Namespace page

## Expected Results
1. Local owner role user can access and display Harvester project/namespace place correctly without hanging to timeout