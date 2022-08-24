---
title: Check the VM is available when Harvester upgrade failed
---

## Category: 
* Harvester Upgrade

## Verification Steps
1. Prepare the previous stable Harvester release cluster
1. Create image
1. Enable Network and create VM
1. Create seveal virtual machine
1. Follow the [official document steps](https://docs.harvesterhci.io/v1.0/upgrade/automatic/) to prepare the online or offline upgrade
1. Do not shutdown virtual machine
1. Start the upgrade
1. Check the VM status if the upgrade failed at `Preload images`, `Upgrade Rancher` and `Upgrade Harvester` phase
1. Check the VM status if the upgrade failed at the `Pre-drain`, `Post-drain` and `RKE2 & OS upgrade` phase

## Expected Results
1. The VM should be work when upgrade failed at `Preload images`, `Upgrade Rancher` and `Upgrade Harvester` phase
1. The VM could not able to function well when upgrade failed at the `Pre-drain`, `Post-drain` and `RKE2 & OS upgrade` phase