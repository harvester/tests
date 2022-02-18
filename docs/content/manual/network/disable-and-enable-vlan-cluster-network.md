---
title: Disable and enable vlan cluster network
---

* Related issues: [#1529](https://github.com/harvester/harvester/issues/1529) Failed to enable vlan cluster network after disable and enable again, display "Network Error"

## Category: 
* Network

## Verification Steps
1. Open settings and config vlan network
1. Enable network and set default harvester-mgmt
1. Disable network
1. Enable network again
1. Check Host, Network and harvester dashboard
1. Repeat above steps several times

## Expected Results
1. User can disable and enable network with default `harvester-mgmt`. 
1. Harvester dashboard and network work as expected

