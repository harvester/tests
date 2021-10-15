---
title: Negative initiate a backup while system is taking another backup
---
1. Start a VM backup, bk-1 of a VM which has data  d1
1. While the backup is in progress, write some more data d2 in the VM disk and initiate another backup bk-2.
1. Verify the backup 1 and backup 2

## Expected Results
1. Backup bk-1 should have only d1 data
1. backup bk-2 should have data d1 and d2