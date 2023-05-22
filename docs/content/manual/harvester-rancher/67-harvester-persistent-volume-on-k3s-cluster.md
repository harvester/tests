---
title: 67-Harvester persistent volume on k3s Cluster	
---

* Related task: [#2755](https://github.com/harvester/harvester/issues/2755#issuecomment-1552842389) Steps to manually install Harvester csi-driver on K3s cluster

### Verify steps
Follow test case `66-Deploy Harvester csi driver to k3s Cluster` to manually install csi-driver on k3s cluster

1. Create a nginx deployment in Workload -> Deployments
1. Create a Persistent Volume Claims, select storage class to `harvester` 
1. Select the `Single-Node Read/Write`

1. Open Harvester Volumes page, check the corresponding volume exists
  ![image](https://github.com/harvester/harvester/assets/29251855/8330c45f-ade1-4819-b2f0-5206e32123b6)

1. Click Execute shell to access Nginx container.
1. Run `dd if=/dev/null of=/test/tmpfile bs=1M count=512`
 ![image](https://user-images.githubusercontent.com/29251855/158934986-c08ddccc-3b33-4508-9861-6d10c5ded3c5.png)

1. Delete the Nginx deployment.

1. Create a standalone PVC on `PersistentVolumeClaims` page with `harvester` storage class

1. Change to Harvester dashboard.
1. Click the Edit config for the volume.
1. Change volume size. We can see the volume is in Resizing status.

1. Delete PVC in k3s dashboard.



## Expected Results

1. Check can deploy nginx service correctly
  ![image](https://github.com/harvester/harvester/assets/29251855/53b606b9-f429-4806-8c5d-4fa2e06e9cf3)


1. Check can correctly create PVC in `PersistenVolumeClaims`
  ![image](https://github.com/harvester/harvester/assets/29251855/631e0977-51e0-491f-9cca-d01f88c41253)


1. Check can correctly create PV in `PersistentVolumes` 
  ![image](https://github.com/harvester/harvester/assets/29251855/d9fb5bf1-debb-4644-8c9d-424cee6a5f22)

1. Check can allocate size in nginx container 
  ![image](https://user-images.githubusercontent.com/29251855/158934986-c08ddccc-3b33-4508-9861-6d10c5ded3c5.png)

1. Check the created stand alone PVC and PV on Rancher and Harvester volumes page
  ![image](https://github.com/harvester/harvester/assets/29251855/a7029c09-84b6-4f49-bd6e-436162eece43)
  ![image](https://github.com/harvester/harvester/assets/29251855/81c74645-2608-4fe4-9efa-bd8a7f34f295)
  ![image](https://github.com/harvester/harvester/assets/29251855/8cf67085-6970-4a6c-a8e1-3f14b52e0b8c)



1. Check can resize and delete volume with harvester storage class
  ![image](https://user-images.githubusercontent.com/29251855/158935263-a8b6fa9e-1f4b-43ae-a687-6df3e34986a1.png)
  ![image](https://user-images.githubusercontent.com/29251855/158935288-67409de3-d5d5-4c9d-af04-421f4153658b.png)

1. Check the related volume should be deleted in Harvester too.