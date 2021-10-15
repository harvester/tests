---
title: Negative node down while migration is in progress	
---
1. Initiate VM migration.
1. While migration is in progress, shut the node where the VM is scheduled.
1. After failure, initiate the migration to another node

## Expected Results
1. Migration should fail but volume data should be intact
1. The VM should be accessible on older node
1. The migration scheduled for another node should work fine
1. The VM should be accessible during and after the migration