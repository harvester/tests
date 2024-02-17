---
title: Migrate back VMs that were on host after taking host out of maintenance mode	
---
### Prerequisite:
Have a Harvester cluster with at least 2 nodes setup.

### Test Steps:
**Given** Create a vm with node selector lets say node-1.

**And** Create a vm without node selector on node-1.

**AND** Write some data into both the VMs.

**When** Put the host node-1 into maintenance mode.

**Then** All the Vms on node-1 should be migrated to other nodes or the node should show warning that the vm with node selector can't migrate.

**When** Take out the node-1 from maintenance and migrate all the Vms back to node-1

**Then** All the vms should be migrated successfully.
