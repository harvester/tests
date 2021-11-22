---
title: 10-Add and grant project-custom user to harvester
---
1. Open `Users & Authentication` 
1. Click `Users` and Create
1. Create user name `project-custom` and set password
1. Select `Standard User` in the Global permission
1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `default` project

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)

1. Search project-custom user
1.  Assign `Custom` role to it

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/70098173-d9b5-43f5-85ab-5011f8c7d7c0)

1. Set `Create Namespace`, `Manage Volumes` and `View Volumes` 
1. Logout current user from Rancher 
1. Login with `project-custom`
1. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-custom` and set password
1. Can assign `Custom` role to `project-custom` in default
1. Can login correctly with `project-custom`
1. Can do `Create Namespace`, `Manage Volumes` and `View Volumes` in default project


