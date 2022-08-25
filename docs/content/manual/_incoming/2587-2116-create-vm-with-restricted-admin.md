---
title: RBAC Create VM with restricted admin user
---

* Related issues: 
- [#2587](https://github.com/harvester/harvester/issues/2587) [BUG] namespace on create VM is wrong when going through Rancher 
- [#2116](https://github.com/harvester/harvester/issues/2116) [BUG] You can see cattle-monitoring-system volumes as restricted admin in Harvester

## Category: 
* Authentication

## Verification Steps
1. Verification Steps
1. Import Harvester into Rancher
1. Create a restricted admin
1. Navigate to Volumes page
1. Verify you only see associated Volumes
1. Log out of admin and log in to restricted admin
1. Navigate to Harvester UI via virtualization management
1. Open virtual machines tab
1. Click create
1. Verified that namespace was default.
1. Create VM

## Expected Results
1. VM should create with no errors