---
title: Verify that VMs stay up when disks are evicted
---

* Related issues: [#1334](https://github.com/harvester/harvester/issues/1334) Volumes fail with Scheduling Failure after evicting disc on multi-disc node

## Verification Steps

1. Created 3 node Harvester setup with ipxe example in KVM/libvirt
1. Added formatted disk to node0 VM
1. Created three VMs on node0
1. Created large files on three VMs to see where they were located with dd if=/dev/urandom of=file1.txt count=5192 bs=1M
1. Checked Longhorn to be sure that some VMs were on new disk
1. Deleted disk from Harvester
1. Checked Longhorn to be sure that disk was marked for eviction
1. Verified that VMs were still available while evicting replicas by running commands from serial console/SSH
1. Verified that disk was removed from Longhorn and VMS were still up.

## Expected Results
1. Disk is removed from Longhorn
1. VMs stay up