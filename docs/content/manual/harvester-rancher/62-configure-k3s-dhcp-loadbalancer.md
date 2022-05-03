---
title: 62-Configure the K3s "DHCP" LoadBalancer service
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
  ![image](https://user-images.githubusercontent.com/29251855/158513105-09ab472b-7cd4-4352-b4e1-84f673ee7088.png)

#### Create a DHCP LoadBalancer
1. Open Kubectl shell.
1. Create `test-dhcp-lb.yaml` file.
    ```
    apiVersion: v1
    kind: Service
    metadata:
        annotations:
        cloudprovider.harvesterhci.io/ipam: dhcp
        name: test-dhcp-lb
        namespace: default
    spec:
        ports:
        - name: http
        nodePort: 30172
        port: 8080
        protocol: TCP
        targetPort: 80
        selector:
        test: test
        sessionAffinity: None
        type: LoadBalancer
    ```
1. Run `k apply -f test-dhcp-lb.yaml` to apply it.
  ![image](https://user-images.githubusercontent.com/29251855/158513659-3e0c487b-c819-492c-8c62-62fc644fd858.png)
1. The Pool LoadBalancer should get an IP from vip-pool and work.
  ![image](https://user-images.githubusercontent.com/29251855/158513800-70d7c0ba-5a4b-4462-90df-c8d05b5a389d.png)

## Expected Results
1. Can create load balance service correctly
1. Can route workload to nginx deployment