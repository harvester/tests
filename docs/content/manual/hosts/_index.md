---
title: Hosts
---
The hosts are the nodes which make the cluster. Currently they have `cos` installed on them. Navigating to the hosts tab in the Harvester UI shows the details of the nodes.

## Negative Test Case Behavior
- If a host goes down
    - The VMs on the host stay in active, or whatever status they were in
    - The host goes to unavailable, but the VM status will not update
    - You can not migrate the VM to a new host, but sometimes a VM will migrate when the host turns back on
- If a host reboots
    - The VM shows as active
    - The host goes to unavailable then to available again as it boots up
- If a host with a replica goes down and the number of replica goes below 3?
- If a host goes into maintenance mode
    - It enters into an `entering maintenance mode` status
    - All the VMs migrate off to other nodes
    - The node goes into maintenance mode
    - If you take it out of maintenance mode you can migrate the VMs back
- I've noticed that the VMs sometimes migrate when you're turning a powered off node on. That might be some queued migration tasks. I'll keep an eye on it
- If you delete a host while it is unavailable and there are VMs on it
    - The host is removed
    - The VMs stay in running with no node assigned for a few minutes, then they are started on a new node
    - If you start a migration with the node down but before you delete it then it goes into a fail state and it doesn't seem to be able to be started on a new node, even if you stop and then start it.
---
