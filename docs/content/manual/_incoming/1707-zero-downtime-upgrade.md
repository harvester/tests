---
title: Zero downtime upgrade 
---

* Related issues: [#1707](https://github.com/harvester/harvester/issues/1707) [BUG] Zero downtime upgrade stuck in "Waiting for VM live-migration or shutdown..."

## Category: 
* Upgrade

## Verification Steps
1. Create a ubuntu image from URL
1. Enable Network with management-mgmt
1. Create a virtual network vlan1 with id 1
1. Setup backup target
1. Create a VM backup
1. Follow the [guide](https://github.com/harvester/docs/blob/main/docs/upgrade/automatic.md) to do upgrade test
![image](https://user-images.githubusercontent.com/29251855/166428121-391f5321-ec8e-46ce-9a96-ea92f04b3907.png)
![image](https://user-images.githubusercontent.com/29251855/166429966-b08cea0e-c457-41b2-a647-b6d3ac00aa58.png)
## Expected Results
1. Can upgrade correctly with all VMs remain in running
![image](https://user-images.githubusercontent.com/29251855/166430303-376d9e30-bf92-49eb-b3e2-8eeeb2375702.png)
![image](https://user-images.githubusercontent.com/29251855/166430680-bb9e14fe-7da5-4b73-9ec8-47a780b4914c.png)