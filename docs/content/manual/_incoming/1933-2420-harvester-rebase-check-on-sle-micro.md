---
title: Harvester rebase check on SLE Micro
---

* Related issues: [#1933](https://github.com/harvester/harvester/issues/1933) [FEATURE] Rebase Harvester on SLE Micro for Rancher

* Related issues: [#2420](https://github.com/harvester/harvester/issues/2420) [FEATURE] support bundle: support SLE Micro OS
  
## Category: 
* System

## Verification Steps
1. Download support bundle in support page 
1. Extract support bundle and check every file content
1. Vagrant install master release
1. Execute backend E2E regression test 
1. Run frontend Cypress automated test against feature Images, Networks, Virtual machines
1. Run manual test against feature Volume, Live migration and Backup and rancher integration

## Expected Results
1. Check can download support bundle correctly, check can access every file without empty
1. Check debug command exists (include necessary packages)
     - k9s
     - kubectl
     - ip
     - lsblk, gisk
     - tar, gzip
     - ctr
     - zstd


1. Version check
     - SLE Micro: 5.2
     - VARIANT_ID: Harvester-20220705

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
1. Major feature smoke test
   - Images
   - Volume
   - Networks
   - Virtual Machine
   - Live migration
   - Backup
   - Rancher integration (master-8f01b558-head, rancher v2.6.5)