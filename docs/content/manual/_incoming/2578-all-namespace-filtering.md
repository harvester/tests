---
title: All Namespace filtering in VM list
---

* Related issues: [#2578](https://github.com/harvester/harvester/issues/2578) [BUG] When first entering the harvester cluster from Virtualization Managements, some vm's in namespace are not shown in the list

## Category: 
* UI

## Verification Steps
1. Create a harvester cluster
1. Create a VM in the default namespace
1. Creating a Namespace (eg: test-vm)
1. Import the Harvester cluster in Rancher
1. access to the harvester cluster from Virtualization Management
1. click Virtual Machines tab


## Expected Results
1. test-vm-1 should also be shown in the list
![image](https://user-images.githubusercontent.com/24985926/181211867-4f3889cd-a14e-463c-9a7f-0aee2d5f358e.png)