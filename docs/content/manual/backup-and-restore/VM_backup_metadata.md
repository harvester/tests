---
title: VM Backup with metadata
---
Ref: https://github.com/harvester/harvester/issues/988

## Verify Items
  - Metadata should be removed along with VM deleted
  - Metadata should be synced after backup target switched
  - Metadata can be used in new cluster


## Case: Metadata create and delete
1. Install Harvester with any nodes
1. Create an image for VM creation
1. Setup NFS/S3 **backup target**
1. Create a VM, then create a backup named `backup1`
1. File `default-backup1.cfg` should be exist in the **backup target** path `<backup root>/harvester/vmbackups`
1. Delete the VM Backup `backup1`
1. File `default-backup1.cfg` should be removed

## Case: Metadata sync after backup target changed
1. Install Harvester with any nodes
1. Create an image for VM creation
1. Setup NFS **backup target**
1. Create VM `vm1`, then create file `tmp` with content `first` in the VM
1. Backup `vm1` named `backup1`
1. Append content `second` into `tmp` file in the VM `vm1`
1. Backup `vm1` named `backup2`
1. Switch **backup target** to S3
1. Delete backups and VM `vm1` in the dashboard
1. Backup Files should be kept in the former **backup target**
1. Swithc **backup target** back
1. Backups should be loaded in Dashboard's Backup page
1. Restore `backup1` to `vm-b1`
1. `vm-b1` should contain file which was created in **Step 4**
1. Restore `backup2` to `vm-b2`
1. `vm-b2` should contain file which was modified in **step 6**
1. Repeat **Step 3** to **Step 16** with following Backup ordering
  - S3 -> NFS
  - NFS -> NFS
  - S3 -> S3

## Case: Backup rebuild in new cluster
1. Repeat **Case: Metadata create and delete** as cluster A to generate backup data
1. Installer another Harvester with any nodes as cluster B
1. setup **backup-target** which contained old backup data
1. **Backup Targets** in _Backups_ should show `Ready` state for all backups.  (this will take few mins depends on network connection)
1. Create image for backup
    1. The image **MUST** use the same `storageClassName` name as the backup created.
    2. `storageClassName` can be found in backup's `volumeBackups` in the YAML definition.
    3. `storageClassName` can be assigned by `metadata.name` when creating image via YAML.
      For example, when you assign `metadata.name` as `image-dgf27`, the `storageClassName` will be named as `longhorn-image-dgf27`
1. Restore backup to new VM
1. VM should started successfully
1. VM should contain those data that it was taken backup
