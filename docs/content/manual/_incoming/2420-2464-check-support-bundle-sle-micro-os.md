---
title: Check support bundle for SLE Micro OS
---

* Related issues: [#2420](https://github.com/harvester/harvester/issues/2420) [FEATURE] support bundle: support SLE Micro OS
* Related issues: [#2464](https://github.com/harvester/harvester/issues/2464) [backport v1.0] [FEATURE] support bundle: support SLE Micro OS

## Category: 
* Support Bundle

## Verification Steps
1. Download support bundle in support page
1. Extract the support bundle, check every file have content
1. ssh to harvester node
1. Check the /etc/os-release file content

## Expected Results
1. Check can download support bundle correctly, check can access every file without empty


1. Checked every harvester nodes, the ID have changed to `sle-micro-rancher`
  - ID=`sle-micro-rancher`

  ```
  harvester-gv2ks:~ # cat /etc/os-release
  NAME="SLE Micro"
  VERSION="5.2"
  VERSION_ID="5.2"
  PRETTY_NAME="Harvester master"
  ID="sle-micro-rancher"
  ID_LIKE="suse"
  ANSI_COLOR="0;32"
  CPE_NAME="cpe:/o:suse:sle-micro-rancher:5.2"
  VARIANT="Harvester"
  VARIANT_ID="Harvester-20220705"
  GRUB_ENTRY_NAME="Harvester master"
  ```