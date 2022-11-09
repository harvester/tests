---
title: VM Snapshot support
category: UI
tag: VM, volume, p1, integration
---
Ref: https://github.com/harvester/harvester/issues/553


### Verify Steps:
1. Install Harvester with any nodes
1. Create an Image for VM creation
1. Create `vm1` with the image and an additional data volume `disk-1`
1. Login to `vm1`, execute following commands:
    - `fdisk /dev/vdb` with new and primary partition
    - `mkfs.ext4 /dev/vdb1`
    - `mkdir vdb && mount -t ext4 /dev/vdb1 vdb`
    - `ping 127.0.0.1 | tee -a test vdb/test`
1. Navigate to _Virtual Machines_ page, click **Take Snapshot** button on `vm1`'s details, named `vm1s1`
1. Execute `sync` on `vm1` and **Take Snapshot** named `vm1s2`
1. Interrupt `ping...` command and `rm test && sync`, then **Take Snapshot** named `vm1s3`
1. Restore 3 snapshots into **New** VM: `vm1s1r`, `vm1s2r` and `vm1s3r`
1. Content of `test` and `vdb/test` should be the same  in VM, and different in other restored VMs.
1. Restore snapshots with **Replace Existing**
1. Content of `test` and `vdb/test` in restored `vm1` from the snapshot, should be the same as the VM restored with the same snapshot.
