---
title: Negative disrupt backup server while restore is in progress
---
1. Initiate a backup restore from NFS server.
1. Disconnect network from NFS server for 5 secs
1. Verify the restore status

## Expected Results
1. The restore is not be interrupted and should complete.
1. Data should be intact