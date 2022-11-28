---
title: Button of `Download KubeConfig` (e2e_fe)
---
Ref: https://github.com/harvester/harvester/issues/1349

## Verify Items
  - Download KubeConfig should not exist in general views
  - Download Kubeconfig should exist in Support page
  - Downloaded file should be named with suffix `.yaml`

## Case: Download KubeConfig
- navigate to every pages to make sure download kubeconfig icon will not appear in header section
- navigate to support page to check `Download KubeConfig` is work normally