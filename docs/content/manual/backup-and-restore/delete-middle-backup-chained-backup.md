---
title: Delete middle backup in chained backup (e2e_be)
---
1. Create a new VM
1. Create a file named 1 and add some data using command `dd if=/dev/urandom of=file1.txt count=100 bs=1M`
1. Compute md5sum : md5sum-1
1. Create a backup
1. Overwrite file 1 
1. Create file 2
1. Compute md5sum for file 1 and file 2 : md5sum-2, md5sum-3
1. Create Backup
1. Overwrite the file 2
1. Create file 3 and compute md5sum for file 2 and file 3 : md5sum-4, md5sum-5
1. Create backup
1. Delete backup 2
1. Validate file 2 and 3 are the same as they were
1. Restore to backup 1
1. Validate that
    - `md5sum -c file1.md5 file2.md5 file3.md5 `
    - file 1 is in original format - md5sum-1
    - file 2 doesn't exist
    - file 3 doesn't exist
1. Validate data by restoring other backups also.


## Expected Results
1. Vm should create
1. All file operations should create
1. Backup should run
1. All file operations should create
1. Backup should run
1. All file operations should create
1. files should be as expected
