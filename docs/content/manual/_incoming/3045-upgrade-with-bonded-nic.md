---
title: Upgrade Harvester on node that has bonded NICs for management interface
---

* Related issues: [#3045](https://github.com/harvester/harvester/issues/3045) [BUG] Harvester Upgrade 1.0.3 to 1.1.0 does not handle multiple SLAVE in BOND for management interface

## Category: 
* Upgrade

## Environment Setup

- This is to be done on a Harvester cluster where the NICs were configured to be bonded on install for the management interface. This can be done in one of two ways.
    - Single node virtualized environment
    - Bare metal environment with at least two NICs (this should really be done on 10gig NICs, but can be done on gigabit)
- Both NICs should be on the same VLAN/network with the same subnet
- Before you do the upgrade you should do the following
    - Install a previously released version of Harvester with at least 2 bonded NICs on install in `balance-tlb`

    ![image](https://user-images.githubusercontent.com/83787952/198138366-472d4432-839a-4d9d-a942-d55fe8f6f6d8.png)
    - Add an image such as [openSUSE Leap](http://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.3/images/openSUSE-Leap-15.3.x86_64-NoCloud.qcow2)
    - Add the bonded management interface as the VLAN interface
    - Create an externally routed VLAN (1 is the default for most networks that don't have explicit VLANs)
    - Create 3 VMs
    - Verify all 3 VMs pass [health checks](https://harvester.github.io/tests/manual/virtual-machines/)
    - Turn off and on the VMs
    - Turn off VMs

## Verification Steps

1. Start an upgrade if the [upgrade-responder](https://github.com/harvester/upgrade-responder) has one already available or set up a custom upgrade via the instructions [here](https://docs.harvesterhci.io/v1.1/upgrade/automatic/#prepare-an-air-gapped-upgrade)

## Expected Results

- The upgrade should complete successfully and the Harvester cluster and all 3 VMs should pass [health checks](https://harvester.github.io/tests/manual/virtual-machines/)