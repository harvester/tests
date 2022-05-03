---
title: 67-Harvester persistent volume on k3s Cluster	
---

* Related task: [#1812](https://github.com/harvester/harvester/issues/1812) K3s cloud provider and csi driver support

### Environment Setup
1. Docker install rancher v2.6.4
1. Create one node harvester with enough resource

### Verify steps
Follow step **1~6** in tets plan `66-Deploy Harvester csi driver to k3s Cluster`

#### Create Nginx workload for testing
1. Create a nginx-csi deployment with image nginx:latest.
  ![image](https://user-images.githubusercontent.com/29251855/158934043-11d94957-5b85-469e-bdf7-5658edfec5d9.png)


1. Create a new PVC in storage tab: 
  ![image](https://user-images.githubusercontent.com/29251855/158934170-8cb212e7-c84c-48d4-a15d-b921a9e6a8fc.png)

1. Complete the nginx deployment, create related PV in Harvester volume
  ![image](https://user-images.githubusercontent.com/29251855/158934469-6b050d39-a45c-493d-9e29-89e16c1cf23d.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934499-6c7d9525-f43a-4426-8786-1e4aec099964.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934531-9c42b704-67cc-4c91-b24e-fa29f7183f05.png)


1. Click Execute shell to access Nginx container.
1. Run `dd if=/dev/zero of=/test/tmpfile bs=1M count=512`
1. Run `dd if=/dev/null of=/test/tmpfile bs=1M count=512`
 ![image](https://user-images.githubusercontent.com/29251855/158934986-c08ddccc-3b33-4508-9861-6d10c5ded3c5.png)

1. Delete the Nginx deployment.

#### Resize and delete volume with harvester storage class
1. Change to Harvester dashboard.
1. Click the Edit config for the volume.
1. Change volume size. We can see the volume is in Resizing status.
![image](https://user-images.githubusercontent.com/29251855/158935263-a8b6fa9e-1f4b-43ae-a687-6df3e34986a1.png)
![image](https://user-images.githubusercontent.com/29251855/158935288-67409de3-d5d5-4c9d-af04-421f4153658b.png)
1. Delete PVC in k3s dashboard.
1. Related volume should be deleted in Harvester too.




## Expected Results
1. Can deploy nginx service with new PVC created
  ![image](https://user-images.githubusercontent.com/29251855/158934469-6b050d39-a45c-493d-9e29-89e16c1cf23d.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934499-6c7d9525-f43a-4426-8786-1e4aec099964.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934531-9c42b704-67cc-4c91-b24e-fa29f7183f05.png)
1. Can allocate size in nginx container 
  ![image](https://user-images.githubusercontent.com/29251855/158934986-c08ddccc-3b33-4508-9861-6d10c5ded3c5.png)
1. Can resize and delete volume with harvester storage class
  ![image](https://user-images.githubusercontent.com/29251855/158935263-a8b6fa9e-1f4b-43ae-a687-6df3e34986a1.png)
  ![image](https://user-images.githubusercontent.com/29251855/158935288-67409de3-d5d5-4c9d-af04-421f4153658b.png)

