---
title: Check logs on Harvester
---

* Related issues: [#2528](https://github.com/harvester/harvester/issues/2528) [BUG] Tons of AppArmor denied messages

## Category: 
* Logging

## Environment Setup

- This should be run on a Harvester node that has been up for a while and has been in use

## Verification Steps
1. SSH to harvester node
1. Execute `journalctl -b -f`
1. Look through logs and verify that there isn't anything generating lots of erroneous messages

## Expected Results
1. There shouldn't be large volumes of erroneous messages