---
title: 07-Add and grant project-owner user to harvester
---
1. Open `Users & Authentication` 
2. Click `Users` and Create
3. Create user name `project-owner` and set password
4. Select `Standard User` in the Global permission
5. Open harvester from `Virtualization Management` page
6. Click `Projects/Namespaces`
7. Edit config of `default` project
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)
8. Search project-owner user
9. Assign `Owner` role to it
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/f3bb7b2d-f687-4cc0-bb98-f286f45ea17b)
10. Logout current user from Rancher 
11. Login with `project-owner`
12. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-owner` and set password
2. Can assign `Owner` role to `project-owner` in default
3. Can login correctly with `project-owner`
4. Can manage all `default` project resources including host, virtual machines, volumes, VM and network 
