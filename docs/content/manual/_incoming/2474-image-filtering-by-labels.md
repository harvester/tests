---
title: Image filtering by labels
---

* Related issues: [#2474](https://github.com/harvester/harvester/issues/2474) [backport v1.0] [FEATURE] Image filtering by labels

## Category: 
* Image

## Verification Steps
1. Upload several images and add related lable
1. Go to the image list page 
1. Add filter according to test plan 1
1. Go to VM creation page 
1. Check the image list and search by name
1. Import Harvester in Rancher
1. Go to cluster management page
1. Create a RKE2 cluster 
1. Check the image list and search by name

## Expected Results
#### Case 1:
The image list page can be filtered by label in the following cases
Same verification result as https://github.com/harvester/harvester/issues/2474#issuecomment-1182781700


* All image list without filter, image list by created time

#### Case 2:
In the VM creation page, 
* Image are lists according to the added time
![image](https://user-images.githubusercontent.com/29251855/178991434-c67a263c-2df6-4e68-ab38-c721fb4aef88.png)

* Can search specific image by name
![image](https://user-images.githubusercontent.com/29251855/178991526-1e93e689-c0b7-498b-a9e3-6154c4a5f910.png)

#### Case 3:
In the provision RKE2 cluster page, 
* Image are lists according to the added time
  ![image](https://user-images.githubusercontent.com/29251855/179019031-8ce19b3e-b633-49e2-9b62-ab6ad1879a29.png)

* Can search specific image by name
![image](https://user-images.githubusercontent.com/29251855/179019130-d6f5e698-fb32-4d81-a7f1-039f803fd180.png)
