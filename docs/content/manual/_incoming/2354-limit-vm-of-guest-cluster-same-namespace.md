---
title: Limit VM of guest cluster in the same namespace
---

* Related issues: [#2354](https://github.com/harvester/harvester/issues/2354) [FEATURE] Limit all VMs of the Harvester guest cluster in the same namespace

## Category: 
* Rancher integration

## Verification Steps
1. Import Harvester from Rancher 
1. Access Harvester via virtualization management 
1. Create a test project and `ns1` namespace 
1. Create two RKE1 node template, one set to default namespace and another set to ns1 namespace
1. Create a RKE1 cluster, select the first pool using the first node template
1. Create another pool, check can't select the second node template 
1. Create a RKE2 cluster, set the first pool using specific namespace 
1. Add another machine pool, check it will automatically assigned the same namespace as the first pool  

## Expected Results
* On RKE2 cluster page, when we select the first machine pool to specific namespace, then the second pool will automatically and can only use the same namespace as the first pool 
  - Using `default` namespace  
    ![image](https://user-images.githubusercontent.com/29251855/177543321-b7ebe517-d18d-469b-953e-d3534109d367.png)
  - Using custrom namespace
    ![image](https://user-images.githubusercontent.com/29251855/177543795-93f419b6-f083-49b2-9374-42de55d5abd7.png)

* On RKE1 node template page, when we create two node template with different namespace 
![image](https://user-images.githubusercontent.com/29251855/177544417-e82410b6-e0c0-47bf-9dd6-8da42bfd4cc4.png)

  - In RKE1 cluster page, pool 1 can select both `rke1-template` and `rke1-template2`
    ![image](https://user-images.githubusercontent.com/29251855/177546440-876c05a6-80a5-4b6b-83c9-d46ff90b8923.png)

  - But pool 2 can't select `rke1-template2` if `rke1-template` have already selected by pool
    ![image](https://user-images.githubusercontent.com/29251855/177546289-a7b7c17e-2e42-47c6-baf4-7811de1b5c62.png)
