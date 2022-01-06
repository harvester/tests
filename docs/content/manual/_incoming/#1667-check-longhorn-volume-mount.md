---
title: Check Longhorn volume mount point
---

* Related issues: [#1667](https://github.com/harvester/harvester/issues/1667) data partition is not mounted to the LH path properly

## Verification Steps
1. Install Harvester node in VM from ISO
1. Check partitions with `lsblk -f`
1. Verify mount point of `/var/lib/longhorn`

## Expected Results
1. Mount point should show `/var/lib/longhorn`
![image](https://user-images.githubusercontent.com/83787952/146290004-0584f817-d9df-4f4d-9069-d3ed4199b30f.png)