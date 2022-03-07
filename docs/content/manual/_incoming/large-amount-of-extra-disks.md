---
title: Auto provision lots of extra disks
---

> :warning: This is a heuristic test plan since real world race condition is hard to reproduce. 
> If you find any better alternative, feel free to update.
>
> This test is better to perform under QEMU/libvirt environment.

* Related issues: [#1718](https://github.com/harvester/harvester/issues/1718) [BUG] Automatic disk provisioning result in unusable ghost disks on NVMe drives

## Category: 
* Storage

## Verification Steps
1. Create a harvester cluster and attach 10 or more extra disks (needs WWN so that they can be identified uniquely).
1. Add [`auto-disk-provision-paths`] setting and provide a value that matches all the disks added from previous step.
1. Wait for minutes for the auto-provisioning process.
1. Eventually, all disks matching the pattern should be partitioned, formatted and mounted successfully.
1. Navigate to longhorn dashboard to see if each disk is successfully added and scheduled.

## Expected Results
1. A large amout of disks can be auto-provisioned simultaneously.

[`auto-disk-provision-paths`]: https://docs.harvesterhci.io/v1.0/settings/settings/#auto-disk-provision-paths-experimental
