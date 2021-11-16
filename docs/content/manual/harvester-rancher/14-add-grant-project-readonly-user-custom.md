---
title: 14-Add and grant project-readonly user to custom project
---

1. Open harvester from `Virtualization Management` page
2. Click `Projects/Namespaces`
3. Edit config of `testProject` project
4. Search project-readonly user
5. Assign `Read Only` role to it
6.  Logout current user from Rancher 
7.  Login with `project-readonly`
8.  Open harvester from `Virtualization Management` page
9.  Change view to `testProject` only

## Expected Results
1. Can assign `Read Only` role to in `testProject` project
2. Can login correctly with `project-readonly`
3. Can't see `Host` page in `testProject` only view
4. Can't create or edit any resource including virtual machines, volumes, Images ... in `testProject` only view