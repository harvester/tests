---
title: Migrate VM from Restored backup
---
Ref: https://github.com/harvester/harvester/issues/1086

## Verify Items
  - VM can be migrate to any node with any times

## Case: Migrate a restored VM
1. Install Harvester with at least 2 nodes
1. setup backup-target with NFS
1. Create image for VM creation
1. Create VM **a**
1. Add file with some data in VM **a**
1. Backup VM **a** as **a-bak**
1. Restore backup **a-bak** into VM **b**
1. Start VM **b** then check added file should exist with same content
1. Migrate VM **b** to another node, then check added file should exist with same content
1. Migrate VM **b** again, then check added file should exist with same content
