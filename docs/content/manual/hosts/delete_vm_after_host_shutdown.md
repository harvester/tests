---
title: Shut down host then delete hosted VM
category: hosts
tag: p0, integration, VM, host
---

Ref: N/A, legacy test case


### Criteria
- [x] VM should created and started successfully
- [x] Node should be unavailable after shutdown
- [x] VM should able to be deleted


## Verify Steps:
1. Install Harvester with at least 2 nodes
2. Create a image for VM creation
3. Create a VM `vm1` and start it
4. `vm1` should started successfully
5. Power off the node hosting `vm1`
6. the node should becomes unavailable on dashboard
7. Delete `vm1`, `vm1` should be deleted successfully