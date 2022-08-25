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
1. The image list page can be filtered by label in the following cases


1. Can fileter using `One key` without value 
  ![image](https://user-images.githubusercontent.com/29251855/178652845-9f86f535-0443-4f33-b495-49dc95e35f82.png)
1. Can filter using `One key` with value 
  ![image](https://user-images.githubusercontent.com/29251855/178652890-c59b0788-6974-4542-a9c6-0c1ac2490a6c.png)

1. Can filter using `Two keys` without value
  ![image](https://user-images.githubusercontent.com/29251855/178653001-98959826-2ab1-4175-bb8b-a04c7c968c99.png)
 
1. Can filter using using `Two keys` and `one key without value`
![image](https://user-images.githubusercontent.com/29251855/178653077-a941fd77-d66b-43ce-8dc5-f7c7d5dbf055.png)

1. Can filter using `Two keys both have values`
![image](https://user-images.githubusercontent.com/29251855/178653192-c22d858f-56a2-4fa4-a841-b47171d9dd88.png)

 
1. Can search specific image by name in the Harvester VM creation page:
![image](https://user-images.githubusercontent.com/29251855/178991526-1e93e689-c0b7-498b-a9e3-6154c4a5f910.png)

 
1. Can search specific image by name in the provision RKE2 cluster page:
![image](https://user-images.githubusercontent.com/29251855/179019130-d6f5e698-fb32-4d81-a7f1-039f803fd180.png)
