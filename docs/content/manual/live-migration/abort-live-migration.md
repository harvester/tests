---
title: Test aborting live migration	
---
1. On a VM that is turned on select migrate
1. Start the migration
1. Abort the migration

## Expected Results
1. You should see the status move to migrating
1. You should see the status move to aborting migration
1. You should see the status move to running
1. The VM should pass health checks