---
title: Verify that vm-force-reset-policy works
---

* Related issues: [#1661](https://github.com/harvester/harvester/issues/1661) vm-force-deletion-policy for vm-force-reset-policy

## Environment setup
Setup an airgapped harvester
1. Create a 3 node harvester cluster 

## Verification Steps
1. Navigate to advanced settings and edit vm-force-reset-policy
![image](https://user-images.githubusercontent.com/83787952/146448317-a259d86d-2020-4bed-adc2-f19ecf0d3fbb.png)
1. Set reset policy to `60`
1. Create VM
1. Run health checks
1. Shut down node that is running VM
1. Check for when it starts to migrate to new Host

## Expected Results
1. It should migrate after 60 seconds