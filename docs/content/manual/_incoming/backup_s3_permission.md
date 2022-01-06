---
title: Backup S3 reduce permissions
---
Ref: https://github.com/harvester/harvester/issues/1339

## Verify Items
  - Backup target connect to S3 should only require the permission to access the specific bucket

## Case: S3 Backup with `single-bucket-user`
1. Install Harvester with any nodes
1. Setup Minio
    1. then follow the [instruction](https://objectivefs.com/howto/how-to-restrict-s3-bucket-policy-to-only-one-aws-s3-bucket) to create a `single-bucket-user`.
    1. Create specific bucket for the user
    1. Create other buckets
1. setup `backup-target` with the **single-bucket-user** permission
    1. When assign the dedicated bucket (for the user), connection should success.
    1. When assign other buckets, connection should failed with **AccessDenied** error message
