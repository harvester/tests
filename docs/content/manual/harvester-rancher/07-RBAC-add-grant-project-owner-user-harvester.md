---
title: 07-Add and grant project-owner user to harvester
---
1. Open `Users & Authentication` 
1. Click `Users` and Create
1. Create user name `project-owner` and set password
1. Select `Standard User` in the Global permission
1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `default` project

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)

1. Search project-owner user
1. Assign `Owner` role to it

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/f3bb7b2d-f687-4cc0-bb98-f286f45ea17b)

1. Logout current user from Rancher 
1. Login with `project-owner`
1. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-owner` and set password
1. Can assign `Owner` role to `project-owner` in default
1. Can login correctly with `project-owner`
1. Can manage all `default` project resources including host, virtual machines, volumes, VM and network 
