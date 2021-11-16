---
title: 16-Add and grant project-custom user to custom project
---

1. Open harvester from `Virtualization Management` page
2. Click `Projects/Namespaces`
3. Edit config of `testProject` project
4. Search project-custom user
5. Assign `Custom` role to it
6. Set `Create Namespace`, `Manage Volumes` and `View Volumes` 
7. Logout current user from Rancher 
8. Login with `project-custom`
9. Open harvester from `Virtualization Management` page
10. Change view to `testProject` only

## Expected Results
1. Can assign `Custom` role to `project-custom` in `testProject` project
2. Can login correctly with `project-custom`
3. Can do `Create Namespace`, `Manage Volumes` and `View Volumes` in `testProject` project


