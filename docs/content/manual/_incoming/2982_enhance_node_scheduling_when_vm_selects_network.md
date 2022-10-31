---
title: enhance node scheduling when vm selects network
category: UI
tags: network, VM settings, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2982

### Criteria
Scheduling rule added automatically when select specific network
![image](https://user-images.githubusercontent.com/5169694/197729616-a6fcda2e-42ba-469f-b6c1-9c297bef1a45.png)


### Verify Steps:
1. go to `Cluster Networks / Config` page,  create a new Cluster Network (eg: test)
1. Create a new `network config` in the `test` Cluster Network. (Select a specific node)
![image.png](https://images.zenhubusercontent.com/60345555ec1db310c78aa2b8/431ba9b2-56e7-48af-bf4d-6e0ba964ebd3)
1. go to `Network` page
1. to create a new network (e.g:  `test-untagged`), select `UntaggedNetwork` type and select `test` cluster network. click `Create` button
1. go to VM create page,    fill all required value,  Click `Networks` tab,   select `default/test-untagged` network,  click `Create` button
1. The VM is successfully created, but the scheduled node may not match the Network Config
![image.png]