---
title: VolumeSnapshot Management
category: UI
tags: VM, p1, functional
---
Ref: https://github.com/harvester/harvester/issues/2296


### Verify Steps:
1. Install Harvester with any nodes
1. Create an Image for VM creation
1. Create vm `vm1` and start it
1. **Take Snapshot* on `vm1` named `vm1s1`
1. Navigate to _Volumes_, click disks of `vm1` then move to **Snapshots** tab, volume of snapshot `vm1s1` should not displayed
1. Navigate to _Advanced/Volume Snapshots_, volumes of snapshot `vm1s1` should not displayed
1. Navigate to _Advanced/VM Snapshots_, snapshot `vm1s1` should displayed
