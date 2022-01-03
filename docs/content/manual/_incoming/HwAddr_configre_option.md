---
title: Install Option `HwAddr` for Network Interface
---
Ref: https://github.com/harvester/harvester/issues/1064

## Verify Items
  - Configure Option `HwAddr` is working on install configuration

### Case: Use `HwAddr` to install harvester via PXE
1. Install Harvester with PXE installation, set `hwAddr` instead of `name` in **install.networks**
2. Harvester should installed successfully
