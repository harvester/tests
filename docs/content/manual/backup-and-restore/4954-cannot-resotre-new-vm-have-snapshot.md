---
title: VM have snapshot can't be restored to new VM
---

* Related issues: [#4954](https://github.com/harvester/harvester/issues/4954) [BUG] VM Restore to new VM doesn't work if there is VM Snapshot


## Category: 
* Backup and Restore

## Verification Steps
1. Prepare a 3 nodes Harvester cluster
1. Create a vm named vm1
1. Setup nfs backup target
1. Create a backup for the vm1
1. Create a snapshot for the vm1
1. Restore the backup of vm1 to create a new VM
1. Check can restore vm correctly
1. Shutdown vm1,
1. Restore the backup of vm to replace the existing vm
1. Select Retain volume
1. Check can restore vm correctly.

## Expected Results
*  Can restore vm backup to create a new vm when already setup vm backup and snapshot on it.

*  Can restore vm backup to replace existing vm (retain volume) when already setup vm backup and snapshot on it.
