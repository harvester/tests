---
title: Upgrade guest cluster kubernetes version can also update the cloud provider chart version
---

* Related issues: [#2546](https://github.com/harvester/harvester/issues/2546) [BUG] Harvester Cloud Provider is not able to deploy upgraded container after upgrading the cluster

## Category: 
* Rancher integration

## Verification Steps
1. Prepare the previous stable Rancher rc version and Harvester  
2. Update `rke-metadata-config` to `{"refresh-interval-minutes":"1440","url":"https://yufa-dev.s3.ap-east-1.amazonaws.com/data.json"}` in global settings
  ![image](https://user-images.githubusercontent.com/29251855/180735267-939e92e3-7fd5-4659-8bc8-ab14c95161d8.png)
3. Update the ui-dashboard-index to `https://releases.rancher.com/dashboard/latest/index.html`
4. Set `ui-offline-preferred` to `Remote`
5. Refresh web page (ctrl + r)
6. Open Create RKE2 cluster page
7.  Check the `show deprecated kubernetes patched versions`
  ![image](https://user-images.githubusercontent.com/29251855/180736528-feaa9615-ccf9-482b-9354-c2c9a6a4b23b.png)
8. Select `v1.23.8+rke2r1` 
9. Finish the RKE2 cluster provision 
  ![image](https://user-images.githubusercontent.com/29251855/180738516-3f429bba-22ab-4476-bebf-0ac2f87935c3.png)
10. Check the current cloud provider version in workload page
  ![image](https://user-images.githubusercontent.com/29251855/180738877-56afcd55-e519-48d9-a8b8-3cbed91a1dfb.png)
11. Edit RKE2 cluster, upgrade the kubernetes version to `1.23.9-rc3+rke2r1`
  ![image](https://user-images.githubusercontent.com/29251855/180739231-e61ef680-5a9d-480b-9ac9-eda7839e17b6.png)
  ![image](https://user-images.githubusercontent.com/29251855/180739331-611b05d4-0c5d-4835-9da0-8c05b9cca027.png)
12. Wait for update finish
  ![image](https://user-images.githubusercontent.com/29251855/180739876-dc409fa8-a9a6-406b-a614-085cea57121f.png)
13. The cloud provider is upgrading
  ![image](https://user-images.githubusercontent.com/29251855/180740637-5d1c6ce0-07ed-4a62-a364-f1b5e9fe473f.png)
14. delete the old cloud provider version pod (v0.1.3)
  ![image](https://user-images.githubusercontent.com/29251855/180740767-e6d5cdc2-c004-4c7a-8298-690775265002.png)
15. Wait for newer version cloud provider have been bumped
  ![image](https://user-images.githubusercontent.com/29251855/180740875-38fa0cc0-c13a-4e39-ba46-5e869eadf087.png)
  ![image](https://user-images.githubusercontent.com/29251855/180740998-80e451e5-ad91-4111-8abe-f51395427b9c.png)



## Expected Results
After upgrading the existing RKE2 guest cluster kubernetes version from older `v1.23.8+rke2r1` to `1.23.9-rc3+rke2r1`.
The Harvester cloud provider can successfully updated from `v0.1.3` to `v0.1.4`  

Cloud provider before upgrade: v0.1.3
  ![image](https://user-images.githubusercontent.com/29251855/180738877-56afcd55-e519-48d9-a8b8-3cbed91a1dfb.png)

After upgrade: v0.1.4
  ![image](https://user-images.githubusercontent.com/29251855/180740998-80e451e5-ad91-4111-8abe-f51395427b9c.png)

