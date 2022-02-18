---
title: Support volume hot plug live migrate
---

* Related issues: [#1401](https://github.com/harvester/harvester/issues/1401) Support volume hot-unplug

## Category: 
* Storage

## Environment setup
Setup an airgapped harvester
1. Create an 3 nodes harvester cluster with large size disks 


## Verification Steps

##### Scenario2: Live migrate VM not have hot-plugged volume before, do hot-plugged the unplugged.


1. Create a virtual machine
1. Create several volumes (without image)
1. Add volume, hot-plug volume to virtual machine
1. Open virtual machine, find hot-plugged volume
1. Click Detach volume
1. Add volume again
1. Migrate VM from one node to another
1. Detach volume
1. Add unplugged volume again

## Expected Results
1. Can hot-plug volume without error
2. Can hot-unplug the pluggable volumes without restarting VM
3. The de-attached volume can also be hot-plug and mount back to VM