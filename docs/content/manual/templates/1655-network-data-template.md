---
title: Verify network data template
---

* Related issues: [#1655](https://github.com/harvester/harvester/issues/1655) When using a VM Template the Network Data in the template is not displayed

## Verification Steps
1. Create new VM template with network data in advanced settings
```
network:
  version: 1
  config:
    - type: physical
      name: interface0
      subnets:
         - type: static
           address: 10.84.99.0/24
           gateway: 10.84.99.254
```
1. Create new VM and select template
1. Verify that network data is in advanced network config

## Expected Results
1. network data should show
![image](https://user-images.githubusercontent.com/83787952/145734902-5e8a9f3c-12b9-4d96-ad5e-42e0f1b94cec.png)