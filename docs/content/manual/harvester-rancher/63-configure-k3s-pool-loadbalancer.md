---
title: 63-Configure the K3s "Pool" LoadBalancer service
---
Prerequisite: 
Already provision K3s cluster and cloud provider on test plan 
* 59-Create K3s Kubernetes Cluster 
* 61-Deploy Harvester cloud provider to k3s Cluster 

#### Create Nginx workload for testing
1. Create a test-nginx deployment with image nginx:latest.
  ![image](https://user-images.githubusercontent.com/29251855/158512919-a35a079a-aa75-4ce8-bac6-a79438a2e112.png)  
1. Add pod label test: test.
  ![image](https://user-images.githubusercontent.com/29251855/158513017-5afc909a-662a-4f4e-b867-2555241a2cbd.png)

#### Create a Pool LoadBalancer
1. Modify vip-pool in Harvester settings.
  ![image](https://user-images.githubusercontent.com/29251855/158514040-bfcd9ff3-964a-4511-94d7-a497ef88848f.png)

1. Open Kubectl shell.
1. Create `test-pool-lb.yaml` file.
    ```
    apiVersion: v1
    kind: Service
    metadata:
      annotations:
        cloudprovider.harvesterhci.io/ipam: pool
      name: test-pool-lb
      namespace: default
    spec:
      ports:
      - name: http
        nodePort: 32155
        port: 8080
        protocol: TCP
        targetPort: 80
      selector:
        test: test
      sessionAffinity: None
      type: LoadBalancer
    ```
1. Run `k apply -f test-pool-lb.yaml` to apply it.
1. The Pool LoadBalancer should get an IP from vip-pool and work.


## Expected Results
1. Can create `Pool` load balance service correctly
1. Can route workload to nginx deployment
  ![image](https://user-images.githubusercontent.com/29251855/158514315-1b570f64-fe18-400e-acc4-56d03bc30e61.png)