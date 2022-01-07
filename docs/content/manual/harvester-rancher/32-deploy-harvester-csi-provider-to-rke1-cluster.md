---
title: 32-Deploy Harvester CSI provider to RKE 1 Cluster
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
1. Install Harvester CSI driver
1. Make sure CSI driver installed complete
```
NAME: harvester-csi-driver
LAST DEPLOYED: Thu Dec 16 03:59:54 2021
NAMESPACE: kube-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Successfully deployed Harvester CSI driver to the kube-system namespace.
---------------------------------------------------------------------
SUCCESS: helm install --namespace=kube-system --timeout=10m0s --values=/home/shell/helm/values-harvester-csi-driver-100.0.0-up0.1.8.yaml --version=100.0.0+up0.1.8 --wait=true harvester-csi-driver /home/shell/helm/harvester-csi-driver-100.0.0-up0.1.8.tgz
```

## Expected Results
1. Provision RKE1 cluster successfully with `Running` status
1. Can install the Harvester CSI driver correctly
