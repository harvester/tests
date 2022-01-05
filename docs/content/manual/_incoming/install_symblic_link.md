---
title: Install Option `install.device` support symbolic link
---
Ref: https://github.com/harvester/harvester/issues/1462

## Verify Items
  - Disk's symbolic link can be used in install configure option `install.device`

## Case: Harvester install with configure symbolic link on `install.device`
1. Install Harvester with any nodes
2. login to console, use `ls -l /dev/disk/by-path` to get disk's link name
3. Re-install Harvester with configure file, with set the disk's link name instead.
4. Harvester should be install successfully
