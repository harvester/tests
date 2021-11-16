---
title: 10-Add and grant project-custom user to harvester
---
1. Open `Users & Authentication` 
2. Click `Users` and Create
3. Create user name `project-custom` and set password
4. Select `Standard User` in the Global permission
5. Open harvester from `Virtualization Management` page
6. Click `Projects/Namespaces`
7. Edit config of `default` project
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)
8. Search project-custom user
9.  Assign `Custom` role to it
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/70098173-d9b5-43f5-85ab-5011f8c7d7c0)
10. Set `Create Namespace`, `Manage Volumes` and `View Volumes` 
11. Logout current user from Rancher 
12. Login with `project-custom`
13. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-custom` and set password
2. Can assign `Custom` role to `project-custom` in default
3. Can login correctly with `project-custom`
4. Can do `Create Namespace`, `Manage Volumes` and `View Volumes` in default project


