---
title: 14-Add and grant project-readonly user to custom project
---

1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `testProject` project
1. Search project-readonly user
1. Assign `Read Only` role to it
1.  Logout current user from Rancher 
1.  Login with `project-readonly`
1.  Open harvester from `Virtualization Management` page
1.  Change view to `testProject` only

## Expected Results
1. Can assign `Read Only` role to in `testProject` project
1. Can login correctly with `project-readonly`
1. Can't see `Host` page in `testProject` only view
1. Can't create or edit any resource including virtual machines, volumes, Images ... in `testProject` only view