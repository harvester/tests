---
title: Check rancher-monitoring-grafana volume size
---

* Related issues: [#2282](https://github.com/harvester/harvester/issues/2282) [BUG] rancher-monitoring-grafana is too small and it keeps growing


## Category: 
* Monitoring

## Verification Steps
1. Harvester cluster running after 24 hours
1. Access Harvester Longhorn dashboard via https://<vip>/dashboard/c/local/longhorn
1. Open the Longhorn UI
1. Open the volume page
1. Check the `rancher-monitoring-grafana` size and usage 
1. Shutdown a management node machine
1. Power on the management node machine
1. Wait for 60 minutes
1. Check the `rancher-monitoring-grafana` size and usage in Longhorn UI
1. Shutdown all management node machines in sequence 
1. Power on all management node machines in sequence
1. Wait for 60 minutes
1. Check the `rancher-monitoring-grafana` size and usage in Longhorn UI

## Expected Results
1. The `rancher-monitoring-grafana` default allocated with `2Gi` and Actual usage `108 Mi` after running after 24 hours
    ![image](https://user-images.githubusercontent.com/29251855/191000121-9c3c640e-7d7f-4d1b-84f6-39745abca0ce.png)

1. Turn off then turn on the specific vip harvester node machine, the The `rancher-monitoring-grafana` keep stable in `107 Mi` after turning on 60 minutes
    ![image](https://user-images.githubusercontent.com/29251855/191011632-06f03787-6bac-4bff-b964-787b414407ab.png)

1. Turn off then turn on all four harvester node machines, the The `rancher-monitoring-grafana` keep stable in `107 Mi` after turning on 60 minutes
    ![image](https://user-images.githubusercontent.com/29251855/191023195-661275d3-1edb-4739-b585-cca23d17a3d9.png)

