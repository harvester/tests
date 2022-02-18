---
title: Set maintenance mode on the last available node shouldn't be allowed
---

* Related issues: [#1014](https://github.com/harvester/harvester/issues/1014) Trying to set maintenance mode on the last available node shouldn't be allowed

## Category: 
* Host

## Verification Steps
1. Create 3 vms located on node2 and node3
![image](https://user-images.githubusercontent.com/29251855/140375836-50cfdb48-a37f-4d86-b931-04983e837cdc.png)

1. Open host page
1. Set node 3 into maintenance mode
1. Wait for virtual machine migrate to node 2
1. Set node 2 into maintenance mode
1. wait for virtual machine migrate to node 1
1. Set node 2 into maintenance mode

## Expected Results
Within 3 nodes and 3 virtual machines testing environment.
Set maintenance from node 3 -> node 2 -> node 1 in sequence 
The final remaining node will prompt `can't enable maintenance in last available node `

![image](https://user-images.githubusercontent.com/29251855/140376151-a93b69f5-a3d6-4120-b754-c39aec4feadf.png)

![image](https://user-images.githubusercontent.com/29251855/140376294-4bf9d0a1-bcf6-4908-b286-0f79f3d9003b.png)

