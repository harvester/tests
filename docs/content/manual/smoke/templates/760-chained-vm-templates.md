---
title: Chain VM templates and images
---

* Related issues: [#760](https://github.com/harvester/harvester/issues/760) cloud config byte limit

## Verification Steps

1. Create a vm and add userData or networkData, test if it works
1. Run VM health checks
1. create a vm template and add userData create a new vm and use the template
1. Run VM health checks
1. use the existing vm to generate a template, then use the template to create a new vm
1. Run VM health Checks

## Expected Results
1. All VM's should create
1. All VM Health Checks should pass