---
title: 08-Add and grant project-readonly user to harvester
---
1. Open `Users & Authentication` 
2. Click `Users` and Create
3. Create user name `project-readonly` and set password
4. Select `Standard User` in the Global permission
5. Open harvester from `Virtualization Management` page
6. Click `Projects/Namespaces`
7. Edit config of `default` project

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)

8. Search project-readonly user
9.  Assign `Read Only` role to it

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/0effd0f6-6e20-4415-801b-03c4c6294a24)

10. Logout current user from Rancher 
11. Login with `project-readonly`
12. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-readonly` and set password
2. Can assign `Read Only` role to `project-readonly` in default
3. Can login correctly with `project-readonly`
4. Can't see `Host` page in harvester
5. Can't create or edit any resource including virtual machines, volumes, Images ...