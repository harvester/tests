---
title: 35-Hot plug and unplug volumes in RKE2 cluster
---
* Related task: [#1396](https://github.com/harvester/harvester/issues/1396) Integration Cloud Provider for RKE1 with Rancher

### Environment Setup
1. Docker install rancher v2.6.3
1. Create one node harvester with enough resource

### Verify Steps

1. Environment preparation as above steps
1. Import harvester to rancher from harvester settings
1. Create cloud credential
1. Create RKE2 cluster as test case #34
1. Access RKE2 cluster 
1. Open charts in Apps & Market page 
1. Install harvester cloud provider and CSI driver 
1. Make sure cloud provider installed complete
1. Switch to All-namespace and check installed apps page
1. Create a new repo and set url to https://charts.bitnami.com/bitnami
![image](https://user-images.githubusercontent.com/29251855/146343516-ff992ee5-9105-42f8-bfa9-42f84a137015.png)

1. Find and deploy `wordpress` in chart 
![image](https://user-images.githubusercontent.com/29251855/146343376-97df8ead-a88e-4493-b78a-b975cc5e21a0.png)

1. Open Global settings in Rancher dashboard 
1. Change the UI-offline preferred to `Remote` 
![image](https://user-images.githubusercontent.com/29251855/146343923-f4051c3a-56b0-4c41-a40e-c664075ed7c0.png)
1. Click ctrl+R to refresh page
1. Access RKE2 cluster 
1. Open `Services` in service discovery
1. Edit the config of wordpress load balancer service
1. Open the Add-on config in load balancer page and save
![image](https://user-images.githubusercontent.com/29251855/146344351-5ea354b7-2931-4b9f-8fe1-40039f008070.png)
1. Check wordpress deployment
1. Check Storage Class page 
1. Check Persistent Volume in storage
1. Open Storage -> PersistentVolumeClaims
1. Open Storage -> PersistentVolume
1. Remove `wordpress` in InstalledApps


## Expected Results
1. Check `harvester` storageClassess exists
![image](https://user-images.githubusercontent.com/29251855/147920973-1f1f4330-5c03-4155-8f87-ce3bc6497d66.png)
1. Check wordpress related persistent volume claims bounded
![image](https://user-images.githubusercontent.com/29251855/147920914-4af12737-143f-4cd6-b311-e20863e16472.png)
1. Check wordpress related persistent volume bounded 
![image](https://user-images.githubusercontent.com/29251855/147920941-04bd99bc-6574-46f0-85b5-e354f56522a4.png)
1. Check related persistentvolumeclaims and persistent volume can be deleted accordingly






