---
title: Check conditions when stop/pause VM
---
* Related issues: [#1987](https://github.com/harvester/harvester/issues/1987)

## Verification Steps

Stop Request should not have failure message
1. Create a VM with `runStrategy: RunStrategyAlways`.
1. Stop the VM.
1. Check there is no `Failure attempting to delete VMI: <nil>` in VM status.

UI should not show pause message
1. Create a VM.
1. Pause the VM.
1. Although the message `The status of pod readliness gate "kubevirt.io/virtual-machine-unpaused" is not "True", but False` is in the VM condition, UI should not show it.
