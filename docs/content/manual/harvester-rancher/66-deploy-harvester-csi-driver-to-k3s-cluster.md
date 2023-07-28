---
title: 66-Deploy Harvester csi driver to k3s Cluster	
---

* Related task: [#2755](https://github.com/harvester/harvester/issues/2755#issuecomment-1552842389) Steps to manually install Harvester csi-driver on K3s cluster


### Reference Document
[Deploying with Harvester K3s Node Driver](https://deploy-preview-309--harvester-preview.netlify.app/dev/rancher/csi-driver/#deploying-with-harvester-k3s-node-driver)

### Verify steps
1. Prepare a Harvester cluster with enough cpu, memory and disks for K3s guest cluster
1. Create a Rancher instance 
1. Import Harvester in Rancher and create cloud credential
1. ssh to Harvester management node 
1. Extract the kubeconfig of Harvester with `cat /etc/rancher/rke2/rke2.yaml` 
1. Change the server value from https://127.0.0.1:6443/ to your VIP 
1. Copy the kubeconfig and add into your local ~/.kube/config file
1. Import Harvester in Rancher
1. Create cloud credential 
1. Provision a k3s cluster 
  ![image](https://github.com/harvester/harvester/assets/29251855/98f9d10f-2307-4aa5-bd47-3e68e03c2232)

1. Provide the login credential in user data
    ```
    password: 123456
    chpasswd: { expire: False }
    ssh_pwauth: True
    ```
1. On K3s, by default will not provide cloud-provider
  ![image](https://github.com/harvester/harvester/assets/29251855/5058509e-f82e-4f98-af39-3d4e7ad54127)

1. Check k3s cluster provisioning in Ready
  ![image](https://github.com/harvester/harvester/assets/29251855/3acc2867-006b-4fa9-ba37-2e663eaaa8d4)


1. Use the new [generate_cloud_provider_config.sh](https://github.com/harvester/harvester-csi-driver/pull/24/files) to generate `cloud-config` content for csi-driver
    ```
    ./generate_cloud_provider_config.sh <serviceaccount name> <namespace>
    
    e.g ./generate_cloud_provider_config.sh k3s default
    
    ```
1. ssh to the k3s guest cluster vm
1. Create the config-files directory
    ```
    mkdir -p /var/lib/rancher/rke2/etc/config-files
    ```

1. Add the cloud-provider-config file from the cloud-config part of output generated from script 
    ```
    vim /var/lib/rancher/rke2/etc/config-files/cloud-provider-config
    ```

1. Access k3s guest cluster on Rancher 
1. Switch to `All Namespace`
1. Open Apps -> Charts
1. Install Harvester CSI Driver from the Rancher marketplace. You do not need to change the cloud-config path. 
    ![image](https://github.com/harvester/harvester/assets/29251855/188af4e3-9735-4c59-868d-2173c1ea3971)

1. Open Storage -> StorageClasses
1. PersistentVolumeClaims page
1. Create a PVC named `test-pvc`, select `Harvester` in the Storage Class
    ![image](https://github.com/harvester/harvester/assets/29251855/cf4e1682-3774-4b57-b897-411f36d1bc44)


## Expected Results
1. Check can successfully install csi-driver on `Installed Apps`
  ![image](https://github.com/harvester/harvester/assets/29251855/4493d3d1-230f-4651-a9ce-cc25eae8459e)


1. Check `Harvester` set to the `default` storage class
  ![image](https://github.com/harvester/harvester/assets/29251855/34489066-ea70-4271-a64f-12e9018aaa95)

1. Check the `test-pvc` exists on `PersistentVolumeClaims` page
1. Check a new pv created on PersistentVolumes  
1. Check the created pv also exists on Harvester Volumes page
