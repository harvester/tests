---
title: Improved resource reservation
category: UI
tags: dashboard, p2, functional
---
Ref: https://github.com/harvester/harvester/issues/2347, https://github.com/harvester/harvester/issues/1700

![image](https://user-images.githubusercontent.com/5169694/174753699-f65e66c6-677b-4a3a-8f71-bfbb7a3b1bb2.png)
![image](https://user-images.githubusercontent.com/5169694/174754418-c5786f38-5909-40ce-8076-c3eddcd3059a.png)


Test Information
----
* Environment: **Baremetal DL160G9 5 nodes**
* Harvester Version: **master-96b90714-head**
* **ui-source** Option: **Auto**

### Verify Steps:
1. Install Harvester with any nodes
1. Login and Navigate to Hosts
1. CPU/Memory/Storage should display **Reserved** and **Used** percentage.
1. Navigate to Host's details
1. Monitor Data should display **Reserved** and **Used** percentage, and should equals to the value in Hosts.
