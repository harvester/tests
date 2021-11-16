---
title: 15-Add and grant project-member user to custom project
---

1. Open harvester from `Virtualization Management` page
2. Click `Projects/Namespaces`
3. Edit config of `testProject` project
4. Search project-member user
5. Assign `Member` role to it
6. Logout current user from Rancher 
7. Login with `project-member`
8. Open harvester from `Virtualization Management` page
9. Change view to `testProject` only

## Expected Results
1. Can assign `Member` role to `project-member` in `testProject` project
2. Can login correctly with `project-member`
3. Can't see `Host` page in `testProject` project
4. Can't create or edit any resource including virtual machines, volumes, Images ... in `testProject` project