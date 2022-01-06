---
title: VM on error state
---
Ref:
- https://github.com/harvester/harvester/issues/1446
- https://github.com/harvester/harvester/issues/982

## Verify Items
  - Error message should displayed when VM can't be scheduled
  - VM's **state** should be changed when host is down

## Case: Create a VM that no Node can host it
1. Install Harvester with any nodes
1. download a image to create VM
1. create a VM with over-commit (consider to over-provisioning feature, double or triple the host resource would be more reliable.)
1. VM should shows **Starting** state, and an alart icon shows aside.
1. hover to the icon, pop-up message should display messages like `0/N nodes are available: n insufficient ...`

## Case: VM's state changed to **Not Ready** when the host is down
1. Install Harvester with 2+ nodes
1. Create an Image for VM creation
1. Create a VM and wait until state becomes **Running**
1. Reboot the node which hosting the VM
1. Node's _State_ should be `In Progress` in _**Hosts**_ page
1. VM's _State_ should be `Not Ready` in _**Virtual Machines**_ page
