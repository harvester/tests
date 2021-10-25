---
title: Backup single VM with node off
---
1. On multi-node setup bring down node that is hosting VM
1. Click take backup in virtual machine list

## Expected Results
1. The backup should complete successfully

## Comments
We do allow taking backup even if the VM is down, as you can take backup when the VM is off, this is because the volume still exists with longhorn's multi replicas, but weneed to check the data integrity.

## Known Bugs
https://github.com/harvester/harvester/issues/1483