---
title: Negative delete backup while restore is in progress
---
1. Create a backup of VM which has data more than 10Gi.
1. Add 2Gi data in the same VM.
1. Initiate deletion of the backup.
1. While deletion is in progress, create another backup

## Expected Results
1. Creation of backup should be prevented as there is a deletion is in progress.
1. Once the deletion is completed, the backup creation should take place