---
title: Check crash dump when there's a kernel panic
---

* Related issues: [#1357](https://github.com/harvester/harvester/issues/1357) Crash dump not written when kernel panic occurs

## Verification Steps

1. Created new single node cluster with 16GB RAM
1. Booted into debug mode from GRUB entry
1. Created several VMs
1. triggered kernel panic with `echo c >/proc/sysrq-trigger`
1. Waited for reboot
1. Verified that dump was saved in `/var/crash`

## Expected Results
1. dump should be saved in `/var/crash`