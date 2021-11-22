---
title: 15-Add and grant project-member user to custom project
---

1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `testProject` project
1. Search project-member user
1. Assign `Member` role to it
1. Logout current user from Rancher 
1. Login with `project-member`
1. Open harvester from `Virtualization Management` page
1. Change view to `testProject` only

## Expected Results
1. Can assign `Member` role to `project-member` in `testProject` project
1. Can login correctly with `project-member`
1. Can't see `Host` page in `testProject` project
1. Can't create or edit any resource including virtual machines, volumes, Images ... in `testProject` project