---
title: 66-Deploy Harvester csi driver to k3s Cluster	
---

* Related task: [#1812](https://github.com/harvester/harvester/issues/1812) K3s cloud provider and csi driver support

### Environment Setup
1. Docker install rancher v2.6.4
1. Create one node harvester with enough resource

### Verify steps
Follow step **1~13** in tets plan `59-Create K3s Kubernetes Cluster`

1. Download the [Generate addon configuration](https://github.com/harvester/harvester-csi-driver/blob/master/deploy/generate_addon.sh) for csi driver
1. ssh to harvester node 1
1. Execute `cat /etc/rancher/rke2/rke2.yaml`  
1. change the server value from https://127.0.0.1:6443 to your node1 IP
1. Copy the kubeconfig and add into your local ~/.kube/config file
1. Generate K3s kubeconfig by running generate addon script
` ./deploy/generate_addon.sh <k3s cluster name> <namespace>`
e.g `./generate_addon.sh k3s-csi-cluster default`
1. Copy the ks3 kubeconfig content start with `cloud-provider-config:` between `addons_include:`
1. ssh to K3s VM
  ![image](https://user-images.githubusercontent.com/29251855/158932912-38297b70-7546-4349-801f-6a4b8b973305.png)

1. Add kubeconfig content to `/etc/kubernetes/cloud-config`file, remember to align the yaml layout
1. Install Harvester csi driver
  ![image](https://user-images.githubusercontent.com/29251855/158550983-61cff655-66a6-4a49-96bd-6e208f4fc9d8.png)
  ![image](https://user-images.githubusercontent.com/29251855/158551034-090cee3d-9bd6-425c-84d8-16f6a66a5c64.png)
  ![image](https://user-images.githubusercontent.com/29251855/158933473-a0172a62-5f7c-4e68-860c-c9cb38275791.png)
  ![image](https://user-images.githubusercontent.com/29251855/158933756-d4198111-ae05-4a7d-8ea8-d21e3f3d2b87.png)




## Expected Results
1. Can deploy K3s cluster on harvester with kubernetes version `v1.23.4+k3s1`
  ![image](https://user-images.githubusercontent.com/29251855/158935474-9d6f1c37-ea59-485d-83f5-6f1b19ebfa98.png)

1. Can correctly install harvester csi driver on K3s cluster
  ![image](https://user-images.githubusercontent.com/29251855/158933473-a0172a62-5f7c-4e68-860c-c9cb38275791.png)
  ![image](https://user-images.githubusercontent.com/29251855/158933756-d4198111-ae05-4a7d-8ea8-d21e3f3d2b87.png)

1. Can deploy nginx service with new PVC created
  ![image](https://user-images.githubusercontent.com/29251855/158934469-6b050d39-a45c-493d-9e29-89e16c1cf23d.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934499-6c7d9525-f43a-4426-8786-1e4aec099964.png)
  ![image](https://user-images.githubusercontent.com/29251855/158934531-9c42b704-67cc-4c91-b24e-fa29f7183f05.png)
1. Can allocate size in nginx container 
  ![image](https://user-images.githubusercontent.com/29251855/158934986-c08ddccc-3b33-4508-9861-6d10c5ded3c5.png)
1. Can resize and delete volume with harvester storage class
  ![image](https://user-images.githubusercontent.com/29251855/158935263-a8b6fa9e-1f4b-43ae-a687-6df3e34986a1.png)
  ![image](https://user-images.githubusercontent.com/29251855/158935288-67409de3-d5d5-4c9d-af04-421f4153658b.png)

