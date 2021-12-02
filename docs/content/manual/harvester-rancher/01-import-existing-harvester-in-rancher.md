---
title: 01-Import existing Harvester clusters in Rancher	
---
This feature have been deprecated which already enhanced and merge to setup from harvester settings
Please refer to [02-Integrate to Rancher from Harvester settings](https://harvesterhci.io/tests/manual/harvester-rancher/02-integrate-rancher-from-harvester-settings/) to test this feature

1. Login rancher dashboard
2. Navigate to Virtual Management Page
3. Click import existing
4. Copy the curl command 
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/08e70d37-e573-47b1-a3d6-0f3615116d48)
1. SSH to harvester master node (user: rancher)
1. Execute the curl command to import harvester to rancher
`curl --insecure -sfL https://192.168.50.82/v3/import/{identifier}.yaml | kubectl apply -f -`
1. Run `sudo chmod 775 /etc/rancher/rke2/rke2.yaml` to solve the permission denied error
1. Run curl command again, you should see the following successful import message
    ```shell
    namespace/cattle-system configured
    serviceaccount/cattle created
    clusterrolebinding.rbac.authorization.k8s.io/cattle-admin-binding created
    secret/cattle-credentials-413137f created
    clusterrole.rbac.authorization.k8s.io/cattle-admin created
    deployment.apps/cattle-cluster-agent created
    service/cattle-cluster-agent created
    ```
1. Check import status in Virtualization Management page on Rancher 

## Expected Results
1. Harvester successfully imported on virtualization management page 
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/2df98c88-8885-4e9d-a5b2-66f27eea8553)
1. Can access Harvester from Rancher dashboard
1. Display `Project/Namespaces` and `RBAC` tab 
![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/89a5277f-24dd-4bf6-b882-b112fad6f80b)