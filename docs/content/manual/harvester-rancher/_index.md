---
title: Harvester Rancher Integration
---
This section illustrates test cases about how Harvester be integrated and managed by Rancher


## Environment Preparation
Prior to integrate Harvester into Racnher, please setup the following requirement

- Install latest Rancher from Docker

    - You can pull the latest rancher docker image 
    ```sudo docker pull rancher/rancher:2.6.2```  
  
    - And start rancher container in open network
    ```$ sudo docker run -d --restart=unless-stopped -p 80:80 -p 443:443 --privileged rancher/rancher:2.6.2```

- Prepare a 3 nodes harvester cluster
    - Suggest using ISO installtion 
    - For vagrant pxe example, please use the recover command
    https://github.com/harvester/issuse/1541  

     

- Configure resource on harvester cluster 
    - Create image by url or upload file
    - Enable network and bind to harvester-mgmt
    - Create a vlan start with id 1
    ![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/48e273e3-e264-4946-bf8d-774107a30382)
    - Add SSH keys
    - Create a virtual machine on newly created vm, confirm can get ip correctly
    ![image.png](https://images.zenhubusercontent.com/61519853321ea20d65443929/04baf5fc-47ee-4dda-bea7-18f3090d9958)
- Initial config on Rancher server
    - Finish the first time login change password steps
    - Change the login url from `localhost` to reachable ip address according to your bind network 

---
