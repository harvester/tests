---
title: Node promotion for topology label
---

* Related issues: [#2325](https://github.com/harvester/harvester/issues/2325) [FEATURE] Harvester control plane should spread across failure domains
  
## Category: 
* Host

## Verification Steps
1. Install first node, the role of this node should be Management Node
1. Install second node, the role of this node should be Compute Node, the second node shouldn't be promoted to Management Node
1. Add label topology.kubernetes.io/zone=zone1 to the first node
1. Install third node, the second node and third node shouldn't be promoted
1. Add label topology.kubernetes.io/zone=zone1 to the second node, the second node and third node shouldn't be promoted
1. Add label topology.kubernetes.io/zone=zone3 to the third node, the second node and third node shouldn't be promoted
1. Change the value of label topology.kubernetes.io/zone from zone1 to zone2 in the second node, the second node and third node will be promoted to Management Node one by one

## Expected Results
Checked can pass the following test scenarios. 

1. Install **first** node, the role of this node should be `Management Node`
    ```
    harv-0715-node1:~ # kubectl get nodes
    NAME              STATUS   ROLES                       AGE     VERSION
    harv-0715-node1   Ready    control-plane,etcd,master   8m19s   v1.21.11+rke2r1
    ```
1. Install **second** node, the role of this node should be `Compute Node`, the second node shouldn't be promoted to `Management Node`
    ```
    harv-0715-node1:~ # kubectl get nodes
    NAME              STATUS   ROLES                       AGE   VERSION
    harv-0715-node1   Ready    control-plane,etcd,master   30m   v1.21.11+rke2r1
    harv-0715-node2   Ready    <none>                      84s   v1.21.11+rke2r1
    ```

1. Add label topology.kubernetes.io/zone=zone1 to the first node
    ![image](https://user-images.githubusercontent.com/29251855/179459635-b7dd16aa-55c1-4a48-a033-e2e30b0a53b0.png)

1. Install **third** node, the **second** node and **third** node shouldn't be promoted
    ```
    harv-0715-node1:~ # kubectl get nodes
    NAME              STATUS   ROLES                       AGE   VERSION
    harv-0715-node1   Ready    control-plane,etcd,master   74m   v1.21.11+rke2r1
    harv-0715-node2   Ready    <none>                      45m   v1.21.11+rke2r1
    harv-0715-node3   Ready    <none>                      29m   v1.21.11+rke2r1
    ```

1. Add label `topology.kubernetes.io/zone=zone1` to the second node, the **second** node and **third** node shouldn't be promoted
The **second** node have automatically add `topology.kubernetes.io/zone=zone1` after joining the cluster
    ![image](https://user-images.githubusercontent.com/29251855/179466270-49a11528-02d5-449e-b86d-12b4d24c5831.png)


1. Add label `topology.kubernetes.io/zone=zone3` to the third node, the second node and third node shouldn't be promoted
    ![image](https://user-images.githubusercontent.com/29251855/179466524-348379e7-3f3d-4f96-9fe8-ec3cc5d0e9de.png)

    ```
    NAME              STATUS   ROLES                       AGE   VERSION
    harv-0715-node1   Ready    control-plane,etcd,master   88m   v1.21.11+rke2r1
    harv-0715-node2   Ready    <none>                      59m   v1.21.11+rke2r1
    harv-0715-node3   Ready    <none>                      43m   v1.21.11+rke2r1
    ```

1. Change the value of label `topology.kubernetes.io/zone` from `zone1` to `zone2` in the second node, the second node and third node will be promoted to Management Node one by one
1. **Second** node set to `zone2`
    ![image](https://user-images.githubusercontent.com/29251855/179468128-26a3ff56-43db-4583-bde1-cba80a6bda2e.png)

1. **Second** node cordened and promoted
    ![image](https://user-images.githubusercontent.com/29251855/179468063-b5d90e54-a545-46a2-8b44-6a78e0a9456f.png)

1. **Third** node cordened and promoted 
    ![image](https://user-images.githubusercontent.com/29251855/179468306-55f6b3fe-c643-4472-a9bf-4e63cb8d0fde.png)

1. **All** nodes are promoted to the `Mangement node`
    ```
    harv-0715-node1:~ # kubectl get nodes
    NAME              STATUS   ROLES                       AGE   VERSION
    harv-0715-node1   Ready    control-plane,etcd,master   93m   v1.21.11+rke2r1
    harv-0715-node2   Ready    control-plane,etcd,master   64m   v1.21.11+rke2r1
    harv-0715-node3   Ready    control-plane,etcd,master   48m   v1.21.11+rke2r1
    ```

