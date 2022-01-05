---
title: Migrate VM from Restored backup
---
Ref: https://github.com/harvester/harvester/issues/1086

## Verify Items
  - VM can be migrate to any node with any times

## Case: Migrate a restored VM
1. Install Harvester with at least 2 nodes
2. setup backup-target with NFS
3. Create image for VM creation
3. Create VM **a**
4. Add file with some data in VM **a**
5. Backup VM **a** as **a-bak**
6. Restore backup **a-bak** into VM **b**
7. Start VM **b** then check added file should exist with same content
8. Migrate VM **b** to another node, then check added file should exist with same content
9. Migrate VM **b** again, then check added file should exist with same content
