---
title: Enable Harvester addons and check deployment state
---

* Related issues: [#5337](https://github.com/harvester/harvester/issues/5337) [BUG] Failed to enable vm-importer, pcidevices and harvester-seeder controller addons, keep stuck in "Enabling" state

## Category: 
* Addons

## Verification Steps
1. Prepare three nodes Harvester cluster
1. Open Advanced -> `Addons` page
1. Access to harvester node machine
1. Switch to root user and open k9s
1. Enable the `vm-importer`, `pci-devices` and `harvester-seeder` addons
1. Check the corresponding jobs and logs
1. Enable rest of the addons `nvidia-driver-toolkit`, `rancher-monitoring` and `rancher-logging`

## Expected Results
* Check the `vm-importer`, `pci-devices` and `harvester-seeder` display in `Deployment Successful`
* Check the `vm-importer-controller`, `pci-devices-controller` and `harvester-seeder` jobs and the related helm-install chart job all running well on the K9s
* Check the `nvidia-driver-toolkit`, `rancher-monitoring` and `rancher-logging` display in `Deployment Successful`
{{< image "images/addons/5337-enable-all-addons.png" >}}
* Check the `nvidia-driver-toolkit`, `rancher-monitoring` and `rancher-logging` jobs and the related helm-install chart job all running well on the K9s

