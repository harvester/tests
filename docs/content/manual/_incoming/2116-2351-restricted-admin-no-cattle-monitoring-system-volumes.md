---
title: Restricted admin should not see cattle-monitoring-system volumes 
---

* Related issues: [#2116](https://github.com/harvester/harvester/issues/2116) [BUG] You can see cattle-monitoring-system volumes as restricted admin in Harvester
* Related issues: [#2351](https://github.com/harvester/harvester/issues/2351) [Backport v1.0] You can see cattle-monitoring-system volumes as restricted admin in Harvester

## Category: 
* Rancher integration

## Verification Steps
1. Import Harvester to Rancher
1. Create restricted admin in Rancher
1. Log out of rancher
1. Log in as restricted admin
1. Navigate to Harvester ui in virtualization management
1. Navigate to volumes page

## Expected Results
* Login Rancher with restricted admin and access Harvester volume page. 
Now it won't display the cattle-monitoring-system volumes. 
  ![image](https://user-images.githubusercontent.com/29251855/174289481-00e74f70-c773-47af-847c-9ca6ecd86e1d.png)


