---
title: Create load balancer on different roles pools in RKE2 cluster
---

* Related issues: [#4678](https://github.com/harvester/harvester/issues/4678) [BUG] Unable to successfully create LoadBalancer service from Guest cluster post 1.2.1 upgrade



## Category: 
* Rancher 

## Verification Steps
1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Ensure the installed Harvester cloud provider version is `0.2.3` or above
1. Create the first pool, specify the `etcd` and `control plane` roles
1. Create the second pool, specify the `work` role only
1. Create a nginx deployment using Harvester storage class
1. Create a load balancer service with dhcp type and bind to nginx deployment
1. Check can install the load balancer
1. Create a standalone load balancer service, set the following annotation
1. Access to the guest cluster VM, check the load balancer service can get `EXTERNAL_IP`

1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Create the first pool, specify the `control plane` role only
1. Create the second pool, specify the `etcd` role only
1. Create the third pool, specify the `worker` role only
1. Repeat the steps 13 - 17 to create load balancer service

1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Create the only one pool, specify the control plane, etcd and workers roles


## Expected Results
*  Control-plane, ETCD and worker in same pool: 
    - Can successfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP


*  Control-plane and ETCD in A pool, worker in B pool:
    - Can successfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP

*  Control-plane in A pool, ETCD in B pool and worker in C pool:
    - Can successfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP