---
title: VM scheduling on Specific node (e2e_fe)
---
Ref: https://github.com/harvester/harvester/issues/1350

## Verify Items
  - Node which is not active should not be listed in **Node Scheduling** list

## Case: Schedule VM on the Node which is **Enable Maintenance Mode**
1. Install Harvester with at least 2 nodes
1. Login and Navigate to _Virtual Machines_
1. Create VM and Select `Run VM on specific node(s)...`
1. All _**Active**_ nodes should in the list
1. Navigate to _Host_ and pick node(s) to **Enable Maintenance Mode**
1. Make sure Node(s) state changed into _**Maintenance Mode**_
1. Repeat step 2 and 3
1. Picked Node(s) should not in the list
1. Revert picked Node(s) to back to state of _**Active**_
1. Repeat step 2 to 4
