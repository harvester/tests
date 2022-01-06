---
title: Create a VM through the Rancher dashboard
---

* Related issues: [#1613](https://github.com/harvester/harvester/issues/1613) VM memory shows NaN Gi

## Verification Steps
1. import harvester into rancher's virtualization management
1. Load Harvester dashboard by going to virtualization management then clicking on harvester cluster
1. Create a new VM on Harvester
1. Validate the following in the VM list page, the form, and YAML>
    1. Memory
    1. CPU
    1. Disk space

## Expected Results
1. VM should create
1. VM should start
1. All specifications should show correctly