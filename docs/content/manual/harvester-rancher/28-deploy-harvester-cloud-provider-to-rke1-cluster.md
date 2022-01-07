---
title: 28-Deploy Harvester cloud provider to RKE1 Cluster	
---

* Related task: [#1396](https://github.com/harvester/harvester/issues/1396) Integration Cloud Provider for RKE1 with Rancher

### Environment Setup
1. Docker install rancher v2.6.3
1. Create one node harvester with enough resource

### Verify steps
1. Environment preparation as above steps
1. Import harvester to rancher from harvester settings
1. Create cloud credential
1. Create RKE1 node template 
![image](https://user-images.githubusercontent.com/29251855/146299688-3875c18f-61d6-48e6-a15e-250d59c177ba.png)
1. Provision a RKE1 cluster, check the `Harvester` as cloud provider 
![image](https://user-images.githubusercontent.com/29251855/146342214-568bf017-e0e2-4b3a-9f38-894eff77d439.png)
1. Access RKE1 cluster 
1. Open charts in Apps & Market page 
1. Install harvester cloud provider
1. Make sure cloud provider installed complete
```
NAME: harvester-cloud-provider
LAST DEPLOYED: Thu Dec 16 03:57:26 2021
NAMESPACE: kube-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
---------------------------------------------------------------------
SUCCESS: helm install --namespace=kube-system --timeout=10m0s --values=/home/shell/helm/values-harvester-cloud-provider-100.0.0-up0.1.7.yaml --version=100.0.0+up0.1.7 --wait=true harvester-cloud-provider /home/shell/helm/harvester-cloud-provider-100.0.0-up0.1.7.tgz
```

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
2. Can install the Harvester cloud provider correctly
![image](https://user-images.githubusercontent.com/29251855/146220089-a261311c-7455-45f6-ac50-3ec9828ce034.png)

