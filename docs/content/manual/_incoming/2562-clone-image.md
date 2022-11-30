---
title: Clone image (e2e_fe)
---

* Related issues: [#2562](https://github.com/harvester/harvester/issues/2562) [[BUG] Image's labels will not be copied when execute Clone

## Category: 
* Images

## Verification Steps
1. Install Harvester with any nodes
1. Create a Image via URL
1. Clone the Image and named image-b
1. Check image-b labels in Labels tab
 

## Expected Results
1. All labels should be cloned and shown in labels tab