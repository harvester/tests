---
title: Mark some features as experimental
---

* Related issues: [#1671](https://github.com/harvester/harvester/issues/1671) Mark external Harvester cluster provisioning support as experimental

## Verification Steps
1. Verify that external Harvester is marked as experiemental
![image](https://user-images.githubusercontent.com/3344618/146233410-d3f11b88-f4fa-4ee8-a0f5-fb6f70f86e70.png)
1. Verify that Cloud Credentials is marked as experimental
![image](https://user-images.githubusercontent.com/3344618/146233518-ae9777a8-0753-4137-8df1-2976a5df72e7.png)

## Expected Results
1. Can hot-plug volume without error
2. Can hot-unplug the pluggable volumes without restarting VM
3. The de-attached volume can also be hot-plug and mount back to VM
