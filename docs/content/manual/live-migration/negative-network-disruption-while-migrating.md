---
title: Negative network disconnection for a short time while migration is in progress	
---
1. Initiate VM migration.
1. While migration is in progress, disconnect network for 5 sec on the node where the VM is scheduled

## Expected Results
1. Migration should resume once the network is up again
1. The VM should be accessible during and after the migration