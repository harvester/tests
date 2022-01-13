---
title: Reboot a cluster and check VIP
---

* Related issues: [#1669](https://github.com/harvester/harvester/issues/1669) Unable to access harvester VIP nor node IP after reboot or fully power cycle node machines (Intermittent)

## Verification Steps
1. Enable VLAN with NIC harvester-mgmt
1. Create VLAN 1
1. Disable VLAN
1. Enable VLAN again
1. shutdown node 3, 2, 1 server machine
1. Wait for 15 minutes
1. Power on node 1 server machine, wait for 20 seconds
1. Power on node 2 server machine, wait for 20 seconds
1. Power on node 3 server machine
1. Check if you can access VIP and each node IP

## Expected Results
1. VIP should load the page and show on every node in the terminal