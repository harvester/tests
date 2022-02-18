---
title: Test NTP server timesync
---

* Related issues: [#1535](https://github.com/harvester/harvester/issues/1535) NTP daemon in host OS

## Environment setup
This should be on at least a 3 node setup that has been running for several hours that had NTP servers setup during install

## Verification Steps

1. SSH into nodes and verify times are close
1. Verify NTP is active with `sudo timedatectl status`

## Expected Results
1. Times should be within a minute of each other
1. NTP should show as active