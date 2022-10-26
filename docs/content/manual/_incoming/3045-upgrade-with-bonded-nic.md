---
title: Upgrade Harvester on node that has bonded NICs for management interface
---

* Related issues: [#3045](https://github.com/harvester/harvester/issues/3045) [BUG] Harvester Upgrade 1.0.3 to 1.1.0 does not handle multiple SLAVE in BOND for management interface

## Category: 
* Upgrade

## Environment Setup

- This is to be done on a Harvester cluster where the NICs were configured to be bonded on install for the management interface

## Verification Steps

1. Install Harvester with at least 2 bonded NICs on install in `balance-tlb`

    ![image](https://user-images.githubusercontent.com/83787952/198138366-472d4432-839a-4d9d-a942-d55fe8f6f6d8.png)
1. Start an upgrade if the responder has one setup or set up a custom upgrade via the instructions [here](https://docs.harvesterhci.io/v1.1/upgrade/automatic/#prepare-an-air-gapped-upgrade)

## Expected Results

- The upgrade should complete successfully and the Harvester cluster should pass sanity checks