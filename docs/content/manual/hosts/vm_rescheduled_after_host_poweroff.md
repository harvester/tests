---
title: Power node triggers VM reschedule
category: hosts
tag: p0, integration, VM, host
---

Ref: N/A, legacy test case, VM is not migrated but rescheduled


### Criteria
- [x] VM should created and started successfully
- [x] Node should be unavailable after shutdown
- [x] VM should be restarted automatically


## Verify Steps:
1. Install Harvester with at least 2 nodes
2. Create a image for VM creation
3. Create a VM `vm1` and start it
4. `vm1` should started successfully
5. Power off the node hosting `vm1`
6. the node should becomes unavailable on dashboard
7. VM `vm1` should be restarted automatically after `vm-force-reset-policy` seconds
