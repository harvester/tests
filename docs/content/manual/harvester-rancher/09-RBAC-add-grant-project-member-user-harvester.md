---
title: 09-Add and grant project-member user to harvester
---
1. Open `Users & Authentication` 
1. Click `Users` and Create
1. Create user name `project-member` and set password
1. Select `Standard User` in the Global permission
1. Open harvester from `Virtualization Management` page
1. Click `Projects/Namespaces`
1. Edit config of `default` project

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/25221ce8-909a-4532-85d0-5a1912528f37)

1. Search project-member user
1.  Assign `Member` role to it

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/cac6a089-833c-4d37-b0da-bd0ad08677c1)

1. Logout current user from Rancher 
1. Login with `project-member`
1. Open harvester from `Virtualization Management` page

## Expected Results
1. Can create `project-member` and set password
1. Can assign `Member` role to `project-member` in default
1. Can login correctly with `project-member`
1. Can't see `Host` page in harvester
1. Can't create or edit any resource including virtual machines, volumes, Images ...