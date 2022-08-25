---
title: Remove Pod Scheduling from harvester rke2 and rke1
---

* Related issues: [#2642](https://github.com/harvester/harvester/issues/2642) [BUG] Remove Pod Scheduling from harvester rke2 and rke1

## Category: 
* Rancher

## Test Information
Test Environment: 1 node harvester on local kvm machine
Harvester version: v1.0-44fb5f1a-head (08/10)
Rancher version: v2.6.7-rc7

## Environment Setup

1. Prepare Harvester master node
1. Prepare Rancher v2.6.7-rc7
1. Import Harvester to Rancher
1. Set ui-offline-preferred: Remote
1. Go to Harvester Support page
1. Download Kubeconfig
1. Copy the content of Kubeconfig

## Verification Steps

### RKE2 Verification Steps
1. Open Harvester Host page then edit host config
1. Add the following key value in the labels page:
    - topology.kubernetes.io/zone: zone_bp
    - topology.kubernetes.io/region: region_bp
![image](https://user-images.githubusercontent.com/29251855/183802450-a790b9a2-3e2c-4559-8f84-b5a768b9c83d.png)
1. Open the RKE2 provisioning page
1. Expand the show advanced
1. Click add Node selector in Node scheduling
1. Use default Required priority
1. Click Add Rule
1. Provide the following key/value pairs
1. topology.kubernetes.io/zone: zone_bp
1. topology.kubernetes.io/region: region_bp
1. Provide the following user data
    ```
    password: 123456
    chpasswd: { expire: False }
    ssh_pwauth: True
    ```
1. Create the RKE2 guest cluster
1. Go to Harvester Virtual Machine page
1. Edit yaml of the RKE2 guest cluster
![image](https://user-images.githubusercontent.com/29251855/183804372-776736cd-d58a-4f16-828f-45903d99af60.png)
1. Check the node affinity label have written into the yaml
![image](https://user-images.githubusercontent.com/29251855/183804693-da78125c-0be8-4775-8665-37e0302877b9.png)
1. Check the guest cluster VM have no error message
![image](https://user-images.githubusercontent.com/29251855/183804967-9e043d1a-cdc1-4233-a32e-63ea04b98125.png)
1. Check can provision RKE2 cluster correctly
![image](https://user-images.githubusercontent.com/29251855/183805796-956e5ee0-129f-41b8-99e1-03764b6f436e.png)


### RKE1 Verification Steps

1. Follow the steps 1 ~ 7 of the RKE2 verification section
1. Go to Rancher Cluster Management page, add the RKE1 node template
1. Click add Node selector in Node scheduling
1. Use default Required priority
1. Click Add Rule
1. Provide the following key/value pairs
    - topology.kubernetes.io/zone: zone_bp
    - topology.kubernetes.io/region: region_bp
![image](https://user-images.githubusercontent.com/29251855/183807452-643faffb-f9f9-46b8-8414-5a8224aa3e66.png)
1. Create the RKE1 guest cluster
1. Go to Harvester Virtual Machine page
1. Edit yaml of the RKE1 guest cluster
1. Check the node affinity label have written into the yaml
![image](https://user-images.githubusercontent.com/29251855/183807763-073b5622-5e77-4b23-989c-b610ff4d0586.png)
1. Check the guest cluster VM have no error message
![image](https://user-images.githubusercontent.com/29251855/183807827-005bd590-5b24-4bf8-a26d-b81a4bbdc3dc.png)
1. Check can provision RKE1 cluster without error
![image](https://user-images.githubusercontent.com/29251855/183808305-d64c828f-7a08-4fc5-ac27-cbb879d57f2f.png)



## Expected Results
- Pod Scheduling did not appear on the RKE1 template provisioning advanced options
![image](https://user-images.githubusercontent.com/29251855/183801086-cc6de3d9-e420-42b5-af47-3ce7a60cd53c.png)

- Pod Scheduling did not appear on the RKE2 provisioning advanced options
![image](https://user-images.githubusercontent.com/29251855/183801181-67d24d86-fbb6-4bc8-9643-c7684a2406db.png)

- Can deploy guest RKE1 cluster vm to specific Harvester node matching the Node scheduling
![image](https://user-images.githubusercontent.com/29251855/183807763-073b5622-5e77-4b23-989c-b610ff4d0586.png)
![image](https://user-images.githubusercontent.com/29251855/183807827-005bd590-5b24-4bf8-a26d-b81a4bbdc3dc.png)

- Can deploy guest RKE2 cluster vm to specific Harvester node matching the Node scheduling
![image](https://user-images.githubusercontent.com/29251855/183804693-da78125c-0be8-4775-8665-37e0302877b9.png)
![image](https://user-images.githubusercontent.com/29251855/183804967-9e043d1a-cdc1-4233-a32e-63ea04b98125.png)

 - Can deploy guest RKE1 cluster vm to specific Harvester node matching the `Node scheduling` with `external kubconfig`

 - Can deploy guest RKE2 cluster vm to specific Harvester node matching the `Node scheduling` with `external kubconfig`

