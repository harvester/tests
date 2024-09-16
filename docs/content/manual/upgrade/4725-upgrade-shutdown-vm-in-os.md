---
title: Upgrade with VM shutdown in the operating system 
---

* Related issues: [#4725](https://github.com/harvester/harvester/issues/4725) [BUG] Upgrade 1.2.0 -> 1.2.1 is stuck in “Waiting for VM live-migration or shutdown...(1 left)” even though there is NO VM running


## Category: 
* Virtual Machines

## Verification Steps
1. Prepare 3 nodes v1.2.1 Harvester cluster
1. Create a Windows server 2022 VM
1. Create a openSUSE leap 15.4 VM
1. Open web console of each VM
1. Login to Windows VM and shutdown machine from menu
1. Login to openSUSE VM , use command to shutdown machine
1. Upgrade Harvester to v1.3.0-rc1
1. Check the upgrade process

## Expected Results
* We can successfully upgrade to from v1.2.1 to v1.3.0-rc1 and remain the OS state, did not encounter stuck in `Waiting form VM live-migration..`