---
title: Check the OS types in Advanced Options
---

* Related issues: [#2776](https://github.com/harvester/harvester/issues/2776) [FEATURE] remove some dead OS types

  
## Category: 
* Network

## Verification Steps
1. Login harvester dashboard
1. Open the VM create page, check the OS type list
1. Open the image create page, check the OS type list
1. Open the template create page, check the OS type list

## Expected Results
1. The following OS types should be removed from list 
   - Turbolinux 
   - Mandriva
   - Xandros

1. In v1.1.0 master  we add the `SUSE Linux Enterprise` in the VM creation page
    ![image](https://user-images.githubusercontent.com/29251855/190973269-764e425f-20be-4cb1-8334-e7af668a7798.png)

1. In the image create page
    ![image](https://user-images.githubusercontent.com/29251855/190973576-bbc25dd7-9ffe-4f8e-92c2-604defe9eb2b.png)

1. In the template create page
    ![image](https://user-images.githubusercontent.com/29251855/190973689-65943f6e-59da-4f45-88dd-3b8cf17ca0e2.png)