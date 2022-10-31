---
title: Support Volume Clone
category: UI
tags: volume, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2293


### Verify Steps:
1. Install Harvester with any nodes
1. Create an Image for VM creation
1. Create `vm1` with the image and an additional data volume `disk-1`
1. Navigate to _Volumes_, clone _disk-0_ and _disk-1_ which attached to `vm1` by clicking `Clone Volume`
1. Create `vm2` with cloned _disk-0_ and _disk-1_
1. `vm2` should started successfully
1. Login to `vm1`, execute following commands:
    - `fdisk /dev/vdb` with new and primary partition
    - `mkfs.ext4 /dev/vdb1`
    - `mkdir vdb && mount -t ext4 /dev/vdb1 vdb`
    - `ping 127.0.0.1 | tee -a vdb/test`
1. Navigate to Volumes, then clone `disk-1` of **vm1** into **vm1-disk-2**
1. Navigate to Virtual Machines, then update `vm1` to add existing volume `vm1-disk-2`
1. Login to `vm1` then mount `/dev/vdb1`(disk-1) and `/dev/vdc1`(disk-2) into _vdb_ and _vdc_
1. test file should be appeared in both folders of _vdb_ and _vdc_
1. test file should not be empty in both folders of _vdb_ and _vdc_