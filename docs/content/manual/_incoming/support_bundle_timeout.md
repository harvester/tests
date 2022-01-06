---
title: Timeout option for support bundle
---
Ref: https://github.com/harvester/harvester/issues/1585

## Verify Items
  - An **Timeout** Option can be configured for support bundle
  - Error message will display when reach timeout

## Case: Generate support bundle but hit timeout
1. Install Harvester with at least 2 nodes
1. Navigate to Advanced Settings, modify `support-bundle-timeout` to `2`
1. Navigate to Support, Click **Generate Support Bundle**, and force shut down one of the node in the mean time.
1. **2** mins later, the function will failed with an Error message pop up as the snapshot
![image](https://user-images.githubusercontent.com/5169694/145191630-27ef156c-d8dd-4480-811c-c1ce39142491.png)
