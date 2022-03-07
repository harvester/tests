---
title: Add extra disks by using raw disks
---
1. Prepare a disk (with WWN) and attach it to the node.
1. Navigate to "Host" > "Edit Config" > "Disks" and open the dropdown menu "Add disks".
1. Choose a disk to add, e.g. `/dev/sda` but not `/dev/sda1`.

## Expected Results
1. The raw disk shall be schedulable as a longhorn disk as a whole (without any partition).
1. Ths raw disk shall be in `provisioned` phase.
1. Reboot the host and the disk shall be reattached and added back as a longhorn disk.
