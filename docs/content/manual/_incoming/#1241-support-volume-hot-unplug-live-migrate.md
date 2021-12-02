---
title: #1241 Http proxy setting download image
---

[#1241](https://github.com/harvester/harvester/issues/1241) Http proxy setting download image

## Environment setup
Setup an airgapped harvester
1. Create an 3 nodes harvester cluster with large size disks 


## Verification Steps
##### Scenario1: Live migrate VM already have hot-plugged volume to new node, then detach (hot-unplug) it

##### Scenario2: Live migrate VM not have hot-plugged volume before, do hot-plugged the unplugged.


1. Create a virtual machine
2. Create several volumes (without image)
3. Add volume, hot-plug volume to virtual machine
4. Open virtual machine, find hot-plugged volume
5. Click Detach volume
6. Add volume again
7. Migrate VM from one node to another
8. Detach volume
9. Add unplugged volume again

## Expected Results
1. Can hot-plug volume without error
2. Can hot-unplug the pluggable volumes without restarting VM
3. The de-attached volume can also be hot-plug and mount back to VM