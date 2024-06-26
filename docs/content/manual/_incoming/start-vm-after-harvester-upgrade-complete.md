---
title: Check can start VM after Harvester upgrade
---

* Related issues: [#2270](https://github.com/harvester/harvester/issues/2270) [BUG] Unable start VM after upgraded v1.0.1 to v1.0.2-rc2

## Category: 
* Harvester Upgrade

## Verification Steps
1. Prepare the previous stable Harvester release cluster
1. Create image
1. Enable Network and create VM
1. Create several virtual machine
1. Follow the [official document steps](https://docs.harvesterhci.io/v1.0/upgrade/automatic/) to prepare the online or offline upgrade
1. Shutdown all virtual machines
1. Start the upgrade
1. Confirm all the upgrade process complete
1. Start all the virtual machines

## Expected Results
* All virtual machine could be correctly started and work as expected