---
title: Delete first backup in chained backup
---
1. Create a new VM
1. Create a file named 1 and add text
1. Create a backup
1. Edit text in file 1
1. create file 2
1. Create Backup
1. Edit file 2 text
1. Create file 3 and add text
1. Create backup
1. Delete backup 1
1. Validate file 2 and 3 are the same as they were
1. Restore to backup 2
1. Validate that
    - `md5sum -c file1-2.md5 file2.md5 file3.md5`
    - file 1 is in second format
    - file 2 is in first format
    - file 3 doesn't exist

## Expected Results
1. Vm should create
1. All file operations should create
1. Backup should run
1. All file operations should create
1. Backup should run
1. All file operations should create
1. files should be as expected