---
title: Restart/Stop VM with in progress Backup
---
* Related issues: [#1702](https://github.com/harvester/harvester/issues/1702) Don't allow restart/stop vm when backup is in progress

## Verification Steps

1. Create a VM.
1. Create a VMBackup for it.
1. Before VMBackup is done, stop/restart the VM. Verify VM can't be stopped/restarted.
