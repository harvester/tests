---
title: Support Volume Hot Unplug (e2e_fe)
---

* Related issues: [#1401](https://github.com/harvester/harvester/issues/1401) Support volume hot-unplug

## Category: 
* Storage

## Environment setup
Setup an airgapped harvester
1. Create an 3 nodes harvester cluster with large size disks 

##### Scenario1: Live migrate VM already have hot-plugged volume to new node, then detach (hot-unplug) it

## Verification Steps
1. Create a virtual machine
2. Create several volumes (without image)
3. Add volume, hot-plug volume to virtual machine
4. Open virtual machine, find hot-plugged volume
5. Click de-attach volume
6. Add volume again

## Expected Results
1. Can hot-plug volume without error
2. Can hot-unplug the pluggable volumes without restarting VM
3. The de-attached volume can also be hot-plug and mount back to VM

