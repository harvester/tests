---
title: Image filtering by labels
---

* Related issues: [#2319](https://github.com/harvester/harvester/issues/2319) [FEATURE] Image filtering by labels

  
## Category: 
* Image

## Verification Steps
1. Upload several images and add related label
1. Go to the image list page 
1. Add filter according to test plan 1
1. Go to VM creation page 
1. Check the image list and search by name
1. Import Harvester in Rancher
1. Go to cluster management page
1. Create a RKE2 cluster 
1. Check the image list and search by name

## Expected Results
#### Test Result 1:
The image list page can be filtered by label in the following cases
1. All image list without filter, image list by created time
    ![image](https://user-images.githubusercontent.com/29251855/190093902-3b9f2627-cd85-49af-8dc6-07f934143297.png)

1. One key, no value 
    ![image](https://user-images.githubusercontent.com/29251855/190094849-d24061b6-c682-428f-b58e-7d9745c75da4.png)

1. One key with value 
    ![image](https://user-images.githubusercontent.com/29251855/190094975-7bb648f3-096a-45f9-ad18-fb5313ac8d1d.png)

1. Two keys, no value
    ![image](https://user-images.githubusercontent.com/29251855/190095123-2b05a1a3-90c2-448b-9223-46855c35e8c6.png)

1. Two keys, one key have no value
    ![image](https://user-images.githubusercontent.com/29251855/190095239-2e77e399-8b75-45ed-9ae6-74bb6fe0197c.png)

1. Two keys with values
    ![image](https://user-images.githubusercontent.com/29251855/190095348-0a4bf56b-4735-4ccf-b54b-77f67fdcaa26.png)

#### Test Result 2:
In the VM creation page, 
1. Image are lists according to the added time
    ![image](https://user-images.githubusercontent.com/29251855/190096010-2aff9cef-d1c3-430e-a2bd-7552051e8a62.png)

1. Can search specific image by name
    ![image](https://user-images.githubusercontent.com/29251855/190096119-d5d9ef5a-b035-4646-82fa-f366050a1163.png)

#### Test Result 3:
In the provision RKE2 cluster page, 
1. Image are lists according to the added time
    ![image](https://user-images.githubusercontent.com/29251855/190097495-4645830d-c943-41f7-b449-1a59d86bb587.png)

1. Can search specific image by name
    ![image](https://user-images.githubusercontent.com/29251855/190097577-c42b6602-4ac0-4956-9da8-5a7227ffee0b.png)