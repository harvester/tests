---
title: ISO installation console UI Display
---

* Related issues: [#2402](https://github.com/harvester/harvester/issues/2402) [FEATURE] Enhance the information display of ISO installation console UI (tty)

  
## Category: 
* Harvester Installer

## Verification Steps
1. ISO install a single node Harvester
1. Monitoring the ISO installation console UI
1. ISO install a three node Harvester cluster
1. Monitoring the ISO installation console UI of the first node
1. Monitoring the ISO installation console UI of the second node
1. Monitoring the ISO installation console UI of the third node

## Expected Results
The ISO installation console UI enhancement can display correctly under the following single and multiple nodes scenarios.

#### Single node harvester
1. Setting up Harvester cluster
    ![image](https://user-images.githubusercontent.com/29251855/186304660-e13f682c-68a0-4d8b-b6b9-a69ccccd492f.png)

1. Finish installation
    ![image](https://user-images.githubusercontent.com/29251855/186321594-0dba5968-6898-4b91-b2c1-ba163411e643.png)

1. Switch to F12 and turn back
    ![image](https://user-images.githubusercontent.com/29251855/186322340-d586b885-5c64-4a86-985e-0a2916debc18.png)
    ![image](https://user-images.githubusercontent.com/29251855/186322482-2aff0cd8-524f-4d8f-a728-2fa25b6acdf0.png)

#### Three nodes harvester cluster
1. Setting up first node 
    ![image](https://user-images.githubusercontent.com/29251855/186342615-81c132c5-a7d3-4266-8315-40a293721a1a.png)

1. first node finished
    ![image](https://user-images.githubusercontent.com/29251855/186343556-b50d46f0-ed03-4fd2-95cb-e9fecf90be4a.png)

1. Second node finished 
    ![image](https://user-images.githubusercontent.com/29251855/186347502-488ef9e3-9c8c-4885-ab06-dd7558624afb.png)
    
1. Third node finished
    ![image](https://user-images.githubusercontent.com/29251855/186349516-15ee3f63-bb7a-449e-bece-9e8699c9a391.png)