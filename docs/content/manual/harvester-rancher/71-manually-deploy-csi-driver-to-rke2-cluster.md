---
title: 71-Manually Deploy Harvester csi driver to RKE2 Cluster	
---

* Related task: [#2755](https://github.com/harvester/harvester/issues/2755#issuecomment-1552839577) Steps to manually install Harvester csi-driver on RKE2 cluster

### Reference Document
[Deploying with Harvester RKE2 Node Driver](https://deploy-preview-309--harvester-preview.netlify.app/dev/rancher/csi-driver/#deploying-with-harvester-rke2-node-driver)

### Verify steps
1. ssh to Harvester management node 
1. Extract the kubeconfig of Harvester with `cat /etc/rancher/rke2/rke2.yaml` 
1. Change the server value from https://127.0.0.1:6443/ to your VIP 
1. Copy the kubeconfig and add into your local ~/.kube/config file
1. Import Harvester in Rancher
1. Create cloud credential 
1. Provision a RKE2 cluster 
  ![image](https://github.com/harvester/harvester/assets/29251855/b3d0f21a-0f7a-40a9-a6af-5cedbdc0a13e)
1. Provide the login credential in user data
    ```
    password: 123456
    chpasswd: { expire: False }
    ssh_pwauth: True
    ```
1. Select cloud-provider to `Default - RKE2 Embedded` (on Rancher 2.6 you need to select to NONE)
  ![image](https://github.com/harvester/harvester/assets/29251855/73009f87-a0c7-4766-90c6-ff1bef8578e5)

1. Check RKE2 cluster provisioning in Ready
1. Use the new [generate_cloud_provider_config.sh](https://github.com/harvester/harvester-csi-driver/pull/24/files) to generate `cloud-config` content for csi-driver
    ```
    ./generate_cloud_provider_config.sh <serviceaccount name> <namespace>
    
    e.g ./generate_cloud_provider_config.sh rke2 default
    
    ```
1. ssh to the RKE2 guest cluster vm
1. Create the config-files directory
    ```
    mkdir -p /var/lib/rancher/rke2/etc/config-files
    ```

1. Add the cloud-provider-config file from the cloud-config part of output generated from script 
    ```
    vim /var/lib/rancher/rke2/etc/config-files/cloud-provider-config
    ```

1. Access RKE2 guest cluster on Rancher 
1. Switch to `All Namespace`
1. Open Apps -> Charts
1. Install Harvester CSI Driver from the Rancher marketplace. You do not need to change the cloud-config path. 
![image](https://github.com/harvester/harvester/assets/29251855/0a02534b-8526-4616-9332-2aad383bc337)
![image](https://github.com/harvester/harvester/assets/29251855/ce0606c4-c676-4ddd-a6b9-8c9c146c6555)

1. Check can successfully install csi-driver on `Installed Apps`
![image](https://github.com/harvester/harvester/assets/29251855/0d2853ed-eadc-47d9-b128-978ebf2cc5ea)

1. Check `Harvester` set to the `default` storage class
![image](https://github.com/harvester/harvester/assets/29251855/ef684d43-c871-4207-b49e-9732b29fc472)

1. Create a nginx deployment in Workload -> Deployments
1. Create a Persistent Volume Claims, select storage class to `harvester` 
1. Select the `Single-Node Read/Write`

1. Create a standalone PVC on `PersistentVolumeClaims` page with `harvester` storage class

## Expected Results
1. Check can deploy nginx service correctly
![image](https://github.com/harvester/harvester/assets/29251855/b1beffb0-eee4-447c-95ff-ecf96790cfa1)

1. Check can correctly create PVC in `PersistenVolumeClaims`
![image](https://github.com/harvester/harvester/assets/29251855/03ad7f37-c016-4d2d-ab27-599b262022ad)

1. Check can correctly create PV in `PersistentVolumes` 
![image](https://github.com/harvester/harvester/assets/29251855/372ec12c-36b8-4251-b559-a0ae0f647cae)

1. Open Harvester Volumes page, check the corresponding volume exists
![image](https://github.com/harvester/harvester/assets/29251855/30752025-d062-4ae6-beee-54be3c90a3fb)

1. Check can correctly create PVC and PV 
  ![image](https://github.com/harvester/harvester/assets/29251855/ac3c12a2-9349-404c-8b2b-b1ca4e4e5a9d)
  ![image](https://github.com/harvester/harvester/assets/29251855/12bfd2f6-d592-4b93-b48f-9a48cdd6a5bf)

1. Check can create corresponding volume on Harvester 
  ![image](https://github.com/harvester/harvester/assets/29251855/def1f0a2-bd9b-4c35-9081-eec32c2234c0)