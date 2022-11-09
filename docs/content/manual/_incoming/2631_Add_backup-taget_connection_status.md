---
title: Add backup-taget connection status
category: UI
tag: dashboard, settings, p1, acceptance
---
Ref: https://github.com/harvester/harvester/issues/2631

Verified this feature has been implemented.

![image](https://user-images.githubusercontent.com/5169694/190369936-c07b0a5f-8685-4813-8108-1032caf09183.png)


Test Information
----
* Environment: **qemu/KVM 2 nodes**
* Harvester Version: **master-032742f0-head**
* **ui-source** Option: **Auto**

### Verify Steps:
1. Install Harvester with any nodes
1. Login to Dashboard then navigate to _Advanced/Settings_
1. Setup a invalid NFS/S3 backup-target, then click **Test connection** button, error message should displayed
1. Setup a valid NFS/S3 backup-target, then click **Test connection** button, notify message should displayed
1. Navigate to _Advanced/VM Backups_, notify message should NOT displayed
1. Navigate to _Advanced/Settings_ and stop the backup-target server, then navigate to _Advanced/VM Backups_, error message should displayed
