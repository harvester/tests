---
title: Nodes with cordoned status should not be in VM migration list
---

* Related issues: [#1501](https://github.com/harvester/harvester/issues/1501) Nodes with cordoned status should not be in the selection list for VM migration

## Category: 
* Host

## Verification Steps
1. Create multiple VMs on two of the nodes
1. Set the idle node to cordoned state 
1. Edit any config of VM, click migrate
1. Check the available node in the migration list 

## Expected Results
Node set in cordoned state will not show up in the available migration list 

![image](https://user-images.githubusercontent.com/29251855/140716353-de5beb61-47c9-42bc-b553-21082f79267f.png)

![image](https://user-images.githubusercontent.com/29251855/140715919-4e8794b6-105a-4a95-b177-1d7b0484ac08.png)

![image](https://user-images.githubusercontent.com/29251855/140716077-4a61ecb1-e167-41a1-aa0b-ccc59814ff0a.png)

