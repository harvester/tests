---
title: Restore backup create new vm (e2e_be)
---
1. Create a new file before restoring the backup and add some data
1. Stop the VM where the backup was taken
1. Navigate to backups list
1. Click restore Backup
1. Select appropriate option
1. Select backup
1. Click restore
1. Validate that new file is no longer present on machine

## Expected Results
1. Backup should restore
1. VM should update to previous backup
1. File should no longer be present
