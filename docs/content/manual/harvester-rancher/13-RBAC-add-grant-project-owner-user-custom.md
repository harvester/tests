---
title: 13-Add and grant project-owner user to custom project
---

1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `testProject` project
1. Search project-owner user
1. Assign `Owner` role to it
1. Logout current user from Rancher 
1. Login with `project-owner`
1. Open harvester from `Virtualization Management` page
1. Change view to `testProject` only

## Expected Results
1. Can assign `Owner` role to `project-owner` in `testProject` project
1. Can manage all `testProject` project resources including host, virtual machines, volumes, VM and network 
