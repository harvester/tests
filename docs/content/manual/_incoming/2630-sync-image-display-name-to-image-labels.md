---
title: Sync image display name to image labels
---

* Related issues: [#2630](https://github.com/harvester/harvester/issues/2630) [FEATURE] Sync image display_name to image labels

  
## Category: 
* Image

## Verification Steps
1. Login harvester dashboard
1. Access the Preference page
1. Enable developer tool 
    ![image](https://user-images.githubusercontent.com/29251855/187353113-495af11e-a3e5-4f8e-b03b-174b4f0660ea.png)
1. Create an ubuntu focal image from url  https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img
    ![image](https://user-images.githubusercontent.com/29251855/187353177-52516c6d-8e68-4ac5-8b40-4006f6460773.png)
1. View API of the created image 
  ![image](https://user-images.githubusercontent.com/29251855/187353338-1f0691f3-b19a-4382-a26f-ab5897842474.png)
1. Check can found the display name in the image API content 
1. Create the same ubuntu focal image from previous url again which would bring the same display name
1. Check would be denied with error message
1. Create a different ubuntu focal image with the same display name 

## Expected Results
1. In image API content, label `harvesterhci.io/imageDisplayName` added to labels, and it's value should be the displayName value
    ![image](https://user-images.githubusercontent.com/29251855/187353496-39c20027-f438-43de-a212-4f38b2dfbbae.png)
1. Image with the same display name in label would be denied by admission webhook "validator.harvesterhci.io"
    ![image](https://user-images.githubusercontent.com/29251855/187354352-ea2f08f3-01a1-4088-899b-d92e25433781.png)
1. Image with the same display name but different url would also be denied 
    ![image](https://user-images.githubusercontent.com/29251855/187355241-845b09b5-953b-4e90-9948-ca8b025a6f5d.png)