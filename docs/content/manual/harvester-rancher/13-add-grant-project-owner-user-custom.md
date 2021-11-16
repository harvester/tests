---
title: 13-Add and grant project-owner user to custom project
---

1. Open harvester from `Virtualization Management` page
2. Click `Projects/Namespaces`
3. Edit config of `testProject` project
4. Search project-owner user
5. Assign `Owner` role to it
6. Logout current user from Rancher 
7. Login with `project-owner`
8. Open harvester from `Virtualization Management` page
9. Change view to `testProject` only

## Expected Results
1. Can assign `Owner` role to `project-owner` in `testProject` project
2. Can manage all `testProject` project resources including host, virtual machines, volumes, VM and network 
