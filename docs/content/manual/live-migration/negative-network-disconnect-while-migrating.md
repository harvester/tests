---
title: Negative network disconnection for a longer time while migration is in progress	
---
1. Initiate VM migration
1. While migration is in progress, disconnect network for 100 sec on the node where the VM is scheduled

## Expected Results
1. Migration should fail but volume data should be intact
1. The VM should be accessible during the migration and should also be accessible once the migration fails