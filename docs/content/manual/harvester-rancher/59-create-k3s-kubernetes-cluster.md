---
title: 59-Create K3s Kubernetes Cluster
---
1. Click Cluster Management
1. Click Cloud Credentials
1. Click create and select `Harvester`
1. Input credential name
1. Select existing cluster in the `Imported Cluster` list
1. Click Create

![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/4a2f6a52-dac7-4a27-84b3-14cbeb4156aa)

1. Click Clusters 
1. Click Create
1. Toggle RKE2/K3s 
1. Select Harvester
1. Input `Cluster Name`
1. Select `default` namespace
1. Select ubuntu image 
1. Select network `vlan1`
1. Input SSH User: `ubuntu`
![image](https://user-images.githubusercontent.com/29251855/166188165-588adc48-fb41-4a01-a59e-9b059eb06949.png)
1. Click `Show Advanced`
1. Add the following user data:
    ```
    password: 123456
    chpasswd: { expire: false }
    ssh_pwauth: true
    ```
    ![image](https://user-images.githubusercontent.com/29251855/166188400-2e5e3051-f5ce-4b40-8497-71d6ff3cfdfa.png)

1. Click the drop down Kubernetes version list
1. Select K3s kubernetes version
    ![image](https://user-images.githubusercontent.com/29251855/165777245-6059f10d-da2f-49d3-9da3-3b72491f7051.png)

1. Click `Advanced`
1. Add `Arguments`
1. Add `cloud-provider=external`
    ![image](https://user-images.githubusercontent.com/29251855/166189212-d422a433-7ac7-4f26-80fd-452c6df966ae.png)
1. Click Create
1. Wait for K3s cluster provisioning complete

## Expected Results
1. Provision K3s cluster successfully with `Running` status
![image](https://user-images.githubusercontent.com/29251855/166189728-d98b92a3-aa0d-44a8-951c-e637f9530031.png)

1. Can acccess K3s cluster to check all resources and services
![image](https://user-images.githubusercontent.com/29251855/166189812-2fa41514-e416-4a0d-91ec-537ecd9a3b00.png)

