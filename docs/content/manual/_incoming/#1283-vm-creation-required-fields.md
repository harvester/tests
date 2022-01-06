---
title: Check VM creation required-fields
---

* Related issues: [#1283](https://github.com/harvester/harvester/issues/1283) Fix required fields on VM creation page

## Verification Steps

1. Create VM without image name and size
1. Create VM without size
1. Create VM wihout image name
1. Create VM without hostname

## Expected Results
1. You should get an error trying to create VM without image name and size
1. You should get an error trying to create VM without image name
1. You should get an error trying to create VM without size
1. You should not get an error trying to create a VM without hostname