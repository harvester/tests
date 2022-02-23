---
title: Restore backup create new vm in another namespace
---
1. Create a VM `vm` in namespace `default`.
1. Create a file `~/test.txt` with content `test`.
1. Create a VMBackup `default-vm-backup` for it.
1. Create a new namepsace `new-ns`.
1. Create a VMRestore `restore-default-vm-backup-to-new-ns` in `new-ns` namespace based on the VMBackup `default-vm-backup` to create a new VM.


## Expected Results
1. A new VM in `new-ns` namespace should be created.
1. It should have the file `~/test.txt` with content `test`.
