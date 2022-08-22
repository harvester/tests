---
title: Negative change backup target while restoring backup
---

* Related issues: [#2560](https://github.com/harvester/harvester/issues/2560) [BUG] VM hanging on restoring state when backup-target disconnected suddenly


## Category: 
* Category

## Verification Steps
1. Install Harvester with any nodes
1. Login to Dashboard then navigate to Advanced/Settings, setup backup-target with NFS or S3
1. Create Image for VM creation
1. Create VM vm1
1. Take Backup vm1b from vm1
1. Restore the backup vm1b to New/Existing VM
1. When the VM still in restoring state, update backup-target settings to Use the default value then setup it back.

## Expected Results
1. You should get an error
![image](https://user-images.githubusercontent.com/5169694/182815277-98baa7bc-42d1-4404-be87-d60f3b6ba1fd.png)
