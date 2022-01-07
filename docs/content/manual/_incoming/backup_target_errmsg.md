---
title: Backup Target error message
---
Ref: https://github.com/harvester/harvester/issues/1051

## Verify Items
  - Backup target should check input before Click **Save**
  - Error message should displayed on edit page when input is wrong

## Case: Connect to invalid Backup Target
1. Install Harvester with any node
1. Login to dashboard, then navigate to **Advanced Settings**
1. Edit **backup-target**,then input invalid data for NFS/S3 and click **Save**
1. The Page should not be redirect to **Advanced Settings**
1. Error Message should displayed under **Save** button
