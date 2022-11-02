---
title: rancher-monitoring status when hosting NODE down
---

* Related issues: [#2243](https://github.com/harvester/harvester/issues/2243) [BUG] rancher-monitoring is unusable when hosting NODE is (accidently) down

  
## Category: 
* Monitoring

## Verification Steps
1. Install a two nodes harvester cluster
1. Check the Initial state of the 2 nodes Harvester cluster
  ```
  harv-node1-0719:~ # kubectl get nodes
  NAME              STATUS   ROLES                       AGE   VERSION
  harv-node1-0719   Ready    control-plane,etcd,master   36m   v1.21.11+rke2r1
  harv-node2-0719   Ready    <none>
  
  harv-node1-0719:~ # kubectl get pods -A | grep monitoring
  cattle-monitoring-system    prometheus-rancher-monitoring-prometheus-0               3/3     Running     0          33m
  cattle-monitoring-system    rancher-monitoring-grafana-d9c56d79b-ckbjc               3/3     Running     0          33m
  
  harv-node1-0719:~ # kubectl get pods prometheus-rancher-monitoring-prometheus-0 -n cattle-monitoring-system -o yaml | grep nodeName
    nodeName: harv-node1-0719
  
  ```
1. Power off both nodes
1. Power on control-plane node (node 1) first, after 10 seconds, power on compute-node (node2)
1. After reboot, `prometheus-rancher-monitoring-prometheus-0` change to `node2`
    ```
    harv-node1-0719:~ # kubectl get pods prometheus-rancher-monitoring-prometheus-0 -n cattle-monitoring-system -o yaml | grep nodeName
    nodeName: harv-node2-0719
    ```
1. Power off compute-node, the "rancher monitoring" is unusable.
    ![image](https://user-images.githubusercontent.com/29251855/179921261-6bb417d4-8f82-458e-bb4e-91c5ba3d064e.png)
    ![image](https://user-images.githubusercontent.com/29251855/179921394-e32786eb-b551-44fa-b9a6-dbd07d2fe623.png)


    ```
    harv-node1-0719:~ # kubectl get pods -n cattle-monitoring-system
    NAME                                                     READY   STATUS        RESTARTS   AGE
    prometheus-rancher-monitoring-prometheus-0               0/3     Init:0/1      0          4s
    rancher-monitoring-grafana-d9c56d79b-cgkwx               3/3     Terminating   0          25m
    rancher-monitoring-grafana-d9c56d79b-db4w8               0/3     Init:0/2      0          12m
    rancher-monitoring-kube-state-metrics-5bc8bb48bd-gc6xf   1/1     Running       1          81m
    rancher-monitoring-operator-559767d69b-xffrj             1/1     Running       1          81m
    rancher-monitoring-prometheus-adapter-8846d4757-w6xds    1/1     Running       1          81m
    rancher-monitoring-prometheus-node-exporter-nrx75        1/1     Running       1          69m
    rancher-monitoring-prometheus-node-exporter-zn8s2        1/1     Running       1          81m
    ```

1. Check the recovery workaround provided on the monitoring document: 
1. Monitoring can be recovered via using CLI commands to delete related PODs forcely, the cluster will deploy new PODs to replace them.
 
    ```
    Delete each none-running POD in namespace cattle-monitoring-system.
    
    $ kubectl delete pod --force -n cattle-monitoring-system prometheus-rancher-monitoring-prometheus-0
    
    harv-node1-0719:~ # kubectl delete pod --force -n cattle-monitoring-system prometheus-rancher-monitoring-prometheus-0
    warning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.
    pod "prometheus-rancher-monitoring-prometheus-0" force deleted
    ```
  
1. Delete all cattle-monitoring-system related pods
    ```
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-grafana-d9c56d79b-db4w8
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-kube-state-metrics-5bc8bb48bd-gc6xf
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-operator-559767d69b-xffrj
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-prometheus-adapter-8846d4757-w6xds
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-prometheus-node-exporter-nrx75
    $ kubectl delete pod --force -n cattle-monitoring-system rancher-monitoring-prometheus-node-exporter-zn8s2
    ```

1. Check the rancher monitoring is running 
    ```
        harv-node1-0719:~ # kubectl get pods -n cattle-monitoring-system 
        NAME                                                     READY   STATUS     RESTARTS   AGE
        prometheus-rancher-monitoring-prometheus-0               3/3     Running    0          118s
        rancher-monitoring-grafana-d9c56d79b-zfh6r               0/3     Init:0/2   0          82s
        rancher-monitoring-kube-state-metrics-5bc8bb48bd-lmq7l   1/1     Running    0          65s
        rancher-monitoring-operator-559767d69b-94vnt             1/1     Running    0          54s
        rancher-monitoring-prometheus-adapter-8846d4757-6v24v    1/1     Running    0          45s
        rancher-monitoring-prometheus-node-exporter-j6v5j        0/1     Pending    0          32s
        rancher-monitoring-prometheus-node-exporter-xhhk4        1/1     Running    0          23s
    ```
1. Wait for several minutes, the `prometheus-rancher-monitoring-prometheus-0` and `rancher-monitoring-grafana` recreated
    ```
        harv-node1-0719:~ # kubectl get pods -n cattle-monitoring-system
        NAME                                                     READY   STATUS    RESTARTS   AGE
        prometheus-rancher-monitoring-prometheus-0               3/3     Running   0          8m20s
        rancher-monitoring-grafana-d9c56d79b-zfh6r               3/3     Running   0          7m44s
        rancher-monitoring-kube-state-metrics-5bc8bb48bd-lmq7l   1/1     Running   0          7m27s
        rancher-monitoring-operator-559767d69b-94vnt             1/1     Running   0          7m16s
        rancher-monitoring-prometheus-adapter-8846d4757-6v24v    1/1     Running   0          7m7s
        rancher-monitoring-prometheus-node-exporter-j6v5j        0/1     Pending   0          6m54s
        rancher-monitoring-prometheus-node-exporter-xhhk4        1/1     Running   0          6m45s
    ```
1. Check the rancher-monitoring chart can display on the dashboard page
    ![image](https://user-images.githubusercontent.com/29251855/179926047-4459747f-cee1-4af5-83f8-f08d93026f8e.png)


## Expected Results
1. This issue exists on latest master release
1. We can use the workaround steps provided in the [monitoring document](https://github.com/w13915984028/docs/blob/84fc5ab1020d7120922424643cff5ea09cff791f/docs/troubleshooting/monitoring.md) by deleting all the `cattle-monitoring-system` related pods

1. Can recover the rancher-monitoring chart when the hosting node is accidentally down. 
![image](https://user-images.githubusercontent.com/29251855/179926047-4459747f-cee1-4af5-83f8-f08d93026f8e.png)

1. Rancher-monitoring pod back to Running state 
    ```
    NAME                                                     READY   STATUS    RESTARTS   AGE
    prometheus-rancher-monitoring-prometheus-0               3/3     Running   0          8m20s
    rancher-monitoring-grafana-d9c56d79b-zfh6r               3/3     Running   0          7m44s
    ```