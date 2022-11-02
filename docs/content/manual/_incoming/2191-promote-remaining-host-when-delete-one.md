---
title: Promote remaining host when delete one
---

* Related issues: [#2191](https://github.com/harvester/harvester/issues/2191) [BUG] Promote fail, cluster stays in Provisioning phase
  
## Category: 
* Host

## Verification Steps
1. Create a 4-node Harvester cluster.
1. Wait for three nodes to become control plane nodes (role is control-plane,etcd,master).
1. Delete one of the control plane nodes.
1. The remaining worker node should be promoted to a control plane node (role is control-plane,etcd,master).

## Expected Results
1. Four nodes Harvester cluster status, before delete one of the control-plane node
    ```
    n1-221021:/etc # kubectl get nodes
    NAME        STATUS   ROLES                       AGE     VERSION
    n1-221021   Ready    control-plane,etcd,master   17h     v1.24.7+rke2r1
    n2-221021   Ready    control-plane,etcd,master   16h     v1.24.7+rke2r1
    n3-221021   Ready    control-plane,etcd,master   15h     v1.24.7+rke2r1
    n4-221021   Ready    <none>                      4m10s   v1.24.7+rke2r1
    ```

1. Delete the third control-plane node, the 4th node can be promoted to control-plane role
    ```
    n1-221021:/etc # kubectl get nodes
    NAME        STATUS   ROLES                       AGE   VERSION
    n1-221021   Ready    control-plane,etcd,master   17h   v1.24.7+rke2r1
    n2-221021   Ready    control-plane,etcd,master   16h   v1.24.7+rke2r1
    n4-221021   Ready    control-plane,etcd,master   11m   v1.24.7+rke2r1
    
    ```
    ![image](https://user-images.githubusercontent.com/29251855/197312556-2ffe22c4-0f0d-407c-9e38-07e46cfc6d2f.png)

    ```
    n1-221021:/etc # kubectl get machines -A
    NAMESPACE     NAME                  CLUSTER   NODENAME    PROVIDERID         PHASE     AGE   VERSION
    fleet-local   custom-00c844d92e49   local     n4-221021   rke2://n4-221021   Running   12m   
    fleet-local   custom-580f66b2735d   local     n2-221021   rke2://n2-221021   Running   16h   
    fleet-local   custom-6c0eaa9d5d67   local     n1-221021   rke2://n1-221021   Running   17h
    ```
