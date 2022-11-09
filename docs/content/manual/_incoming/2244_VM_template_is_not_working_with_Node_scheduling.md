---
title: VM template is not working with Node scheduling
category: UI
tag: VM, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2244

![image](https://user-images.githubusercontent.com/5169694/177742575-31730953-5ffd-4018-b5ce-1b1e487ee14c.png)


### Verify Steps:
1. Install Harvester with any nodes
1. Create an Image for VM creation
1. Create VM with _**Multiple Instance**_ and _**Use VM Template**_, In **Node Scheduling** tab, select `Run VM on specific node(s)`
1. Created VMs should be scheduled on the specific node
