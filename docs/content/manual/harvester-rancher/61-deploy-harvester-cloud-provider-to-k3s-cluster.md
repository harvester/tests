---
title: 61-Deploy Harvester cloud provider to k3s Cluster	
---

* Related task: [#1812](https://github.com/harvester/harvester/issues/1812) K3s cloud provider and csi driver support

### Environment Setup
1. Docker install rancher v2.6.4
1. Create one node harvester with enough resource

### Verify steps
Follow step **1~13** in tets plan `59-Create K3s Kubernetes Cluster`

1. Click the Edit yaml button
  ![image](https://user-images.githubusercontent.com/29251855/166190410-47331a84-1d4e-4478-9d85-e68a3da91626.png)
1. Set `disable-cloud-provider: true` to disable default k3s cloud provider.
  ![image](https://user-images.githubusercontent.com/29251855/158510820-4d8a0021-1675-4c92-86b9-a6427f2e382b.png)
1. Add `cloud-provider=external` to use harvester cloud provider.
  ![image](https://user-images.githubusercontent.com/29251855/158511002-47a4a532-7f67-4eb0-8da4-074c6d9752e9.png)
1. Create K3s cluster 
![image](https://user-images.githubusercontent.com/29251855/158511706-1c0c6af5-8909-4b1d-bc2a-0fa2fa26e000.png)
1. Download the [Generate addon configuration](https://github.com/harvester/cloud-provider-harvester/blob/master/deploy/generate_addon.sh) for cloud provider 
1. Download Harvester kubeconfig and add into your local ~/.kube/config file 
1. Generate K3s kubeconfig by running generate addon script 
  ` ./deploy/generate_addon.sh <k3s cluster name> <namespace>`
  e.g `./generate_addon.sh k3s-focal-cloud-provider default`
1. Copy the kubeconfig content 
1. ssh to K3s VM
  ![image](https://user-images.githubusercontent.com/29251855/158534901-8fd22159-6a04-4592-ba25-ba4d73742a20.png)
1. Add kubeconfig content to `/etc/kubernetes/cloud-config` file, remember to align the yaml layout
1. Install Harvester cloud provider 
  ![image](https://user-images.githubusercontent.com/29251855/158512528-42ff575a-87a6-4424-bfb5-fa7af94ea74d.png)
  ![image](https://user-images.githubusercontent.com/29251855/158512667-18b0249c-f859-4ae4-96b7-42ce873cb97a.png)


## Expected Results
1. Can install the Harvester cloud provider on k3s cluster correctly
  ![image](https://user-images.githubusercontent.com/29251855/158512758-d06df2f6-7094-4d41-b960-d50b26cd23fb.png)

