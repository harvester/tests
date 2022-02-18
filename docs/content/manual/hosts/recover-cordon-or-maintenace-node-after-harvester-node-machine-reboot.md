---
title: Recover cordon and maintenace node after harvester node machine reboot
---

* Related issues: [#1493](https://github.com/harvester/harvester/issues/1493) When hosts are stuck in maintenance mode and the cluster is unstable you can't access the UI

## Category: 
* Host

## Verification Steps
1. Create 3 virtual machine on 3 harvester nodes
1. Cordon 1st and 2nd node, 
![image](https://user-images.githubusercontent.com/29251855/141106858-cdfb35f3-50af-48d0-b776-1f1cc5dfcedc.png)
1. Enable maintenance mode on 1st and 2nd node 
![image](https://user-images.githubusercontent.com/29251855/141106968-e4d7a6be-6c60-4771-aabd-8df0ccafe252.png)
1. We can't cordon and enable maintenance node on the remaining node 
![image](https://user-images.githubusercontent.com/29251855/141107044-774166b8-117e-4635-b8a2-eeedb65e48fc.png)
1. Reboot 1st and 2nd node bare machine
1. Wait for harvester machine back to service
1. Login dashboard
1. Disable maintenance mode on 1st and 2nd node

## Expected Results
1. Cordon node and enter maintenance mode, after machine reboot, user can login harvester dashboard. 
1. Node remain it's original status
1. Can disable/uncordon node, it can back to original status
![image](https://user-images.githubusercontent.com/29251855/141111698-64d9d648-9018-4c14-8828-539f6e44361e.png)

