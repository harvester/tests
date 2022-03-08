---
title: Multiple Disks Swapping Paths
---

* Related issues: [#1874](https://github.com/harvester/harvester/issues/1874) Multiple Disks Swapping Paths

## Verification Steps
1. Prepare a harvester cluster (single node is sufficient)
1. Prepare two additional disks and format both of them.
1. Hotplug both disks and add them to the host via Harvester Dashboard ("Hosts" > "Edit Config" > "Disks")
1. Shutdown the host.
1. Swap the address and slot of the two disks in order to make their dev paths swapped
    - For libvirt environment, you can swap `<address>` and `<target>` in the XML of the disk.
1. Reboot the host
1. Navigate to the "Host" page, both disks should be healthy and scheduled.

## Expected Results
1. Disks should be healthy and `scheduable` after paths swapped.
