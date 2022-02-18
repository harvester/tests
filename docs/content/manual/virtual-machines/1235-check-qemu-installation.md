---
title: Validate QEMU agent installation
---

* Related issues: [#1235](https://github.com/harvester/harvester/issues/1235) QEMU agent is not installed by default when creating VMs

## Verification Steps

1. Creat openSUSE VM
1. Start VM
1. check for qemu-ga package
1. Create Ubuntu VM 
1. Start VM
1. Check for qemu-ga package

## Expected Results
1. VMs should start
1. Packages should be present