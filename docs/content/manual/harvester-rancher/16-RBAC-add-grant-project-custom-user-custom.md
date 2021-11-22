---
title: 16-Add and grant project-custom user to custom project
---

1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `testProject` project
1. Search project-custom user
1. Assign `Custom` role to it
1. Set `Create Namespace`, `Manage Volumes` and `View Volumes` 
1. Logout current user from Rancher 
1. Login with `project-custom`
1. Open harvester from `Virtualization Management` page
1. Change view to `testProject` only

## Expected Results
1. Can assign `Custom` role to `project-custom` in `testProject` project
1. Can login correctly with `project-custom`
1. Can do `Create Namespace`, `Manage Volumes` and `View Volumes` in `testProject` project


