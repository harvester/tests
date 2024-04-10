---
title: Create load balancer on different roles pools in RKE2 cluster
---

* Related issues: [#4678](https://github.com/harvester/harvester/issues/4678) [BUG] Unable to successfully create LoadBalancer service from Guest cluster post 1.2.1 upgrade



## Category: 
* Rancher 

## Verification Steps
1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Create the first pool, specify the `etcd` and `control plane` roles
1. Create the second pool, specify the `work` role only
1. Add the following cloud config in the `User Data` of each pool
    ```
    write_files:
    - encoding: b64
    content: {harvester's kube config, the cluster namespace should be same as the pool you created (base64 enconded)}
    owner: root:root
    path: /etc/kubernetes/cloud-config
    permission: '0644'
    ```
1. Get the Harvester kubeconfig file, remember to add the namespace (should be the same with the guest cluster)
    ```
    contexts:
    - name: "local"
    context:
    user: "local"
    cluster: "local"
    namespace: "default" ---------------------> Add this line
    ```
1. Output the Harvester kubeconfig into base64 format without new line
    ```
    cat local.yaml | base64 -w 0
    ```
1. Copy the base64 encoded kubeconfig to the cloud config write file sections above
{{< image "images/rancher/4678-base64-kubeconfig.png" >}}
1. Provision the RKE2 guest cluster
1. After pools are created, we remove the harvester-cloud-provider in Apps > Installed Apps (kube-system namesapce).
1. Add new charts in Apps > Repositories, use https://charts.harvesterhci.io to install and select 0.2.3.
{{< image "images/rancher/4678-add-harvester-repo.png" >}}
1. Install Harvester cloud provider 0.2.3 from market
{{< image "images/rancher/4678-install-cloud-provider.png" >}}
1. Create a nginx deployment using Harvester storage class
1. Create a load balancer service with dhcp type and bind to nginx deployment
1. Check can install the load balancer
1. Create a standalone load balancer service, set the following annotation
1. Access to the guest cluster VM, check the load balancer service can get `EXTERNAL_IP`

1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Create the first pool, specif the `control plane` role only
1. Create the second pool, specify the `etcd` role only
1. Create the third pool, specify the `worker` role only
1. Repeat the steps 13 - 17 to create load blancer service

1. Prepare three nodes Harvester and import with Rancher
1. Provision a RKE2 guest cluster in Rancher
1. Create the only one pool, specif the control plane, etcd and workers roles


## Expected Results
*  Control-plane, ETCD and worker in same pool: 
    - Can sucessfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP


*  Control-plane and ETCD in A pool, worker in B pool:
    - Can sucessfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP

*  Control-plane in A pool, ETCD in B pool and worker in C pool:
    - Can sucessfully create LoadBalancer service on RKE2 guest cluster
    - All load balance type service have assigned the EXTERNAL_IP