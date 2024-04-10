---
title: Restore the snapshot when the vm already been restored from backup
---

* Related issues: [#4604](https://github.com/harvester/harvester/issues/4604) [BUG] Restore from snapshot not work if target VM is restore-replaced from backup


## Category: 
* Backup and Restore

## Verification Steps
1. Config backup-target to NFS backup target
1. Create VM, wait VM to Running state
1. Take Backup, wait backup Ready
1. Take VM Snapshot, wait snapshot Ready
1. Stop VM, wait VM Off
1. Restore (Replace) from backup, wait VM Running
1. Stop VM again
1. Restore from snapshot, replace the current VM
1. Check the vm is running
1. Restore from snapshot, create a new VM
1. Check the new vm is created and running

## Expected Results
* Can restore the snapshot to replace original vm when the vm have been restored from backup


* Can restore the snapshot to create the new vm when the vm when the vm have been restored from backup
