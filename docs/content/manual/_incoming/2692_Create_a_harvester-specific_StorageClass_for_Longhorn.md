---
title: Create a harvester-specific StorageClass for Longhorn
category: UI
tag: VM, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/2692

![image](https://user-images.githubusercontent.com/5169694/192323716-c863af2a-388f-49d6-8636-d57f8abbad35.png)


### Verify Steps:
1. Install Harvester with 2+ nodes
1. Login to Dashboard and create an image for VM creation
1. Navigate to _Advanced/Storage Classes_, `harvester-longhorn` and `longhorn` should be available, and `harvester-longhorn` should be settled as **Default**
1. Navigate to _Volumes_ and create `vol-old` where Storage Class is `longhorn` and `vol-new` where Storage Class is `harvester-longhorn`
1. Create VM `vm1` attaching `vol-old` and `vol-new`
1. Login to `vm1` and use `fdisk` format volumes and mount to folders: `old` and `new`
1. Create file and move into both volumes as following commands:
```bash
dd if=/dev/zero of=file1 bs=10485760 count=10
cp file1 old && cp file1 new
```
1. Migrate `vm1` to another host, migration should success
1. Login to `vm1`, volumes should still attaching to folders `old` and `new`
1. Execute command `sha256sum` on `old/file1` and `new/file1` should show the same value.
