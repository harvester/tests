---
title: VM's CPU maximum limitation
---
Ref: https://github.com/harvester/harvester/issues/1565

## Verify Items
  - VM's maximum CPU amount should not have limitation.

## Case: Create VM with large CPU amount
1. Install harvester with any nodes
1. Create image for VM creation
1. Create a VM with vCPU over than 100
1. Start VM and verify `lscpu` shows the same amount
