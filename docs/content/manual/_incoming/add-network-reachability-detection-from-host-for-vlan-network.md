---
title: Add network reachability detection from host for the VLAN network 
---

 * Related issue: [#1476](https://github.com/harvester/harvester/issues/1476) Add network reachability detection from host for the VLAN network 

## Category: 
* Network

## Environment Setup
* The network environment must have vlan network configured and also have DHCP server prepared on your testing vlan

## Verification Steps
1. Enable virtual network with `harvester-mgmt` in harvester
1. Create VLAN 806 with id `806` and set to default `auto` mode
1. Import harvester to rancher
1 .Create cloud credential
1. Provision a rke2 cluster to harvester 
![image](https://user-images.githubusercontent.com/29251855/145564732-0a3cee15-a264-407f-800a-df2e7c649846.png)

![image](https://user-images.githubusercontent.com/29251855/145564961-c921f341-2c88-44cc-9c5e-08789e594552.png)

1. Deploy a `nginx` server workload 
![image](https://user-images.githubusercontent.com/29251855/145565066-c9701c25-c0c6-4077-9718-80279d1d9765.png)

![image](https://user-images.githubusercontent.com/29251855/145565122-41f2fa46-b6de-4a54-bd4e-afe2b9cc6bef.png)

1. Open Service Discover -> Services 
1. Create a Load Balancer service
![image](https://user-images.githubusercontent.com/29251855/145565240-40cd93d7-aadb-4aed-9b99-e0878f014071.png)

1. Provide service port 
![image](https://user-images.githubusercontent.com/29251855/145565319-64191c22-6961-4332-ab13-a6373b4c3814.png)

1. Provide health check port
![image](https://user-images.githubusercontent.com/29251855/145565383-934f3170-c141-4ebc-bffa-3afb7f32282e.png)

1. Edit yaml on nginx workload , copy the lable key value pair
![image](https://user-images.githubusercontent.com/29251855/145565663-c768bedc-9286-408c-9a6b-6fc11056a225.png)

1. Open `Selectors` tab in loadbalncer 
1. Paste the key value pair from nginx 
![image](https://user-images.githubusercontent.com/29251855/145565921-199188c8-0eb7-4ae4-9630-4219eea8cecf.png)

![image](https://user-images.githubusercontent.com/29251855/145565961-0cd66b49-7c20-4036-a4c2-d5f34dfe3a18.png)

1. Open Cluster -> Nodes
1. Access the RKE2 nodes
![image](https://user-images.githubusercontent.com/29251855/145566203-38f44c55-ee39-4095-a8fb-946efdcb3176.png)

1. Click the `Download SSH key`
1. unzip the ssh key 
1. Run `ssh -i <id_rsa> to login rke2 cluster 
1. Access RKE2 cluster 
https://docs.rancher.cn/docs/rke2/cluster_access/_index/
1. Run `./kubectl get svc` 
1. ssh to harvester node 1
1. Run `kubectl get endpointslice -o wide` 
1. Run `curl http://{nigix endpoint ip}
1. Run `curl http://{loadbalcner external ip}

## Expected Results
Currently can access nginx deployment and loadbalancer from harvester node. 

**Access rke2-cluster nodes** 
```
hpd8s7:/home/rancher # kubectl get endpointslice -o wide
NAME                                    ADDRESSTYPE   PORTS   ENDPOINTS                                AGE
kubernetes                              IPv4          6443    10.84.44.114,10.84.44.115,10.84.44.116   44h
kubernetes-default-nginx-lb2-3e4eb608   IPv4          30905   10.84.45.115                             27h
kubernetes-default-ngnix-lb-616792a7    IPv4          30904   10.84.45.115
```

```
hpd8s7:/home/rancher # curl http://10.84.44.115
<a href="https://10.84.44.115/">Found</a>.
```

**Access loadbalancer on rke2-cluster**
```
root@rke2-cluster-pool1-bde93828-k7fzs:/var/lib/rancher/rke2/bin# ./kubectl get svc
NAME         TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)        AGE
kubernetes   ClusterIP      10.43.0.1      <none>         443/TCP        29h
nginx-lb2    LoadBalancer   10.43.87.126   10.84.45.117   80:30905/TCP   27h
ngnix-lb     LoadBalancer   10.43.61.34    10.84.45.116   80:30904/TCP   29h
```
