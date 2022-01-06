---
title: Add/remove disk to Host config
---

* Related issues: [#1623](https://github.com/harvester/harvester/issues/1623) Unable to add additional disks to host config

## Environment setup
1. Add Disk that isn't assigned to host 

## Verification Steps
1. Head to "Hosts" page
1. Click "Edit Config" on a node and switch to "Disks" tab
1. Validate: Open dropdown and see no disks
1. Attach a disk on that node
1. Validate: Open dropdown and see some disks
1. Verify that host shows new disk as available storage and Longhorn is showing new schedulable space
1. Detach a disk on that node
1. Validate: Open dropdown and see no disks
1. Verify that host shows new disk as available storage and Longhorn is showing new schedulable space

## Expected Results
1. Disk space should show appropriately
![image](https://user-images.githubusercontent.com/83787952/146289651-3c8b8da7-5ba1-4a15-aa4f-32f24af4b8dc.png)