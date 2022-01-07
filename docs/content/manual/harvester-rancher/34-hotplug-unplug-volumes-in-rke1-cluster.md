---
title: 34-Hot plug and unplug volumes in RKE1 cluster
---
* Related task: [#1396](https://github.com/harvester/harvester/issues/1396) Integration Cloud Provider for RKE1 with Rancher

### Environment Setup
1. Docker install rancher v2.6.3
1. Create one node harvester with enough resource

### Verify Steps

1. Environment preparation as above steps
2. Import harvester to rancher from harvester settings
3. Create cloud credential
4. Create RKE1 node template 
![image](https://user-images.githubusercontent.com/29251855/146299688-3875c18f-61d6-48e6-a15e-250d59c177ba.png)
5. Provision a RKE1 cluster, check the `Harvester` as cloud provider 
![image](https://user-images.githubusercontent.com/29251855/146342214-568bf017-e0e2-4b3a-9f38-894eff77d439.png)
6. Access RKE1 cluster 
7. Open charts in Apps & Market page 
8. Install harvester cloud provider and CSI driver 
9. Make sure cloud provider installed complete
12. Switch to All-namespace and check installed apps page
13. create a new repo and set url to https://charts.bitnami.com/bitnami
![image](https://user-images.githubusercontent.com/29251855/146343516-ff992ee5-9105-42f8-bfa9-42f84a137015.png)

14. Find and deploy `wordpress` in chart 
![image](https://user-images.githubusercontent.com/29251855/146343376-97df8ead-a88e-4493-b78a-b975cc5e21a0.png)

15. Open Global settings in Rancher dashboard 
16. Change the UI-offline preferred to `Remote` 
![image](https://user-images.githubusercontent.com/29251855/146343923-f4051c3a-56b0-4c41-a40e-c664075ed7c0.png)
17. Click ctrl+R to refresh page
18. Access RKE1 cluster 
18. Open `Services` in service discovery
19. Edit the config of wordpress load balancer service
20. Open the Add-on config in load balancer page and save
![image](https://user-images.githubusercontent.com/29251855/146344351-5ea354b7-2931-4b9f-8fe1-40039f008070.png)
21. Check wordpress deployment
22. Check Storage Class page 
23. Check Persistent Volume in storage
24. Open Storage -> PersistentVolumeClaims
25. Open Storage -> PersistentVolume
26. Remove `wordpress` in InstalledApps


## Expected Results
1. Check `harvester` storageClassess exists
![image](https://user-images.githubusercontent.com/29251855/147917863-9e3c712e-0684-42e7-8b07-e87e8f7eb8f3.png)
1. Check wordpress related persistent volume claims bounded
![image](https://user-images.githubusercontent.com/29251855/147917875-66bd3426-0ccc-4a4d-920a-30e7b856abd3.png)
1. Check wordpress related persistent volume bounded 
![image](https://user-images.githubusercontent.com/29251855/147917907-a6a1f8a0-d116-46a6-b256-1fec8010c268.png)
1. Check related persistentvolumeclaims and persistent volume can be deleted accordingly




