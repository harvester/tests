---
title: Negative Restore a backup while VM is restoring
---

* Related issues: [#2559](https://github.com/harvester/harvester/issues/2559) [BUG] Backup unable to be restored and the VM can't be deleted

## Category: 
* Backup/Restore

## Verification Steps
1. Install Harvester with any nodes
1. Login to Dashboard then navigate to Advanced/Settings, setup backup-target with NFS or S3
1. Create Image for VM creation
1. Create VM vm1
1. Take backup from vm1 as vm1b
1. Take backup from vm1 as vm1b2
1. Click Edit YAML of vm1b, update field status.source.spec.spec.domain.cpu.cores, increase 1
1. Stop VM vm1
1. Restore backup vm1b2 with Replace Existing
1. Restore backup vm1b with Replace Existing when the VM vm1 still in state restoring

## Expected Results
1. You should get an error when trying to restore.
![image](https://user-images.githubusercontent.com/5370752/182722180-3e2f606b-beef-4f8b-8f33-8d235587db4b.png)