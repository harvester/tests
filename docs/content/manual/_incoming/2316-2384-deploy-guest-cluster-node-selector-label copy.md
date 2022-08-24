---
title: Deploy guest cluster to specific node with Node selector label
---

* Related issues: [#2316](https://github.com/harvester/harvester/issues/2316) [BUG] Guest cluster nodes distributed across failure domain
* Related issues: [#2384](https://github.com/harvester/harvester/issues/2384) [backport v1.0.3] Guest cluster nodes distributed across failure domains

## Category: 
* Rancher integration

## Verification Steps
### RKE2 Verification Steps
1. Open Harvester Host page then edit host config 
1. Add the following key value in the labels page:
  - topology.kubernetes.io/zone: zone_bp
  - topology.kubernetes.io/region: region_bp
  ![image](https://user-images.githubusercontent.com/29251855/179735384-77e99870-92ad-41c2-b414-a872130c0b27.png)
1. Open the RKE2 provisioning page 
1. Expand the show advanced 
1. Click add Node selector in `Node scheduling`
1. Use default `Required` priority
1. Click Add Rule
1. Provide the following key/value pairs
  - `topology.kubernetes.io/zone: zone_bp`
  - `topology.kubernetes.io/region: region_bp`
  ![image](https://user-images.githubusercontent.com/29251855/179736419-78612fd1-9990-44d8-b9be-d9a850bd27a0.png)

1. Provide the following user data 
  ```
  password: 123456
  chpasswd: { expire: False }
  ssh_pwauth: True
  ```
1. Create the RKE2 guest cluster
1. Go to Harvester Virtual Machine page
1. Edit yaml of the RKE2 guest cluster 
  ![image](https://user-images.githubusercontent.com/29251855/179737541-f921d841-13ee-4a97-b096-5e4bdca39320.png)
  Check the node affinity label have written into the yaml 
  ![image](https://user-images.githubusercontent.com/29251855/179737712-9c0dac59-78be-4386-b1e4-646d7d7fbd90.png)
1. Check the guest cluster VM have no error message
1. Check can provision RKE2 cluster without error
  ![image](https://user-images.githubusercontent.com/29251855/179739296-33f3292b-3eb9-4823-80e2-64d3e3014765.png)

1. Provide mismatch or not exists node scheduling or pod scheduling selector key/value pair in step 13 or 18
1. Provision another RKE2 cluster 
1. Check VM should have error icon with message and automatically suspend the RKE2 provisioning

### RKE1 Verification Steps
1. Follow the steps 1 ~ 7 of the RKE2 verification section
1. Go to Rancher Cluster Management page, add the RKE1 node template
1. Click add Node selector in `Node scheduling`
1. Use default `Required` priority
1. Click Add Rule
1. Provide the following key/value pairs
  - `topology.kubernetes.io/zone: zone_bp`
  - `topology.kubernetes.io/region: region_bp`
  ![image](https://user-images.githubusercontent.com/29251855/179751217-773ffbaf-6df8-44c2-b4fe-382df4508c38.png)
1. Create the RKE1 guest cluster
1. Go to Harvester Virtual Machine page
1. Edit yaml of the RKE1 guest cluster 
1. Check the node label have written into the yaml 
1. Check the guest cluster VM have no error message
1. Check can provision RKE1 cluster without error
1. Provide mismatch or not exists node scheduling or pod scheduling selector key/value pair in step 6 and 10
1. Provision another RKE1 cluster 
1. Check VM should have error icon with message and automatically suspend the RKE1 provisioning



## Expected Results
- [x] **Can** deploy guest RKE1 cluster vm to specific Harvester node matching the `node scheduling` and `pod scheduling` selector
- [x] **Can** deploy guest RKE2 cluster vm to specific Harvester node matching the `node scheduling` and `pod scheduling` selector
- [x] **Can't** deploy guest RKE1 cluster vm to specific Harvester node if any of the `node scheduling` and `pod scheduling` selector not found on the Harvester node
- [x] **Can't** deploy guest RKE2 cluster vm to specific Harvester node if any of the `node scheduling` and `pod scheduling` selector not found on the Harvester node


