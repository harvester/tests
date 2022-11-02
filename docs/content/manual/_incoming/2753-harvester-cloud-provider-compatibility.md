---
title: Harvester Cloud Provider compatibility check
---

* Related issues: [#2753](https://github.com/harvester/harvester/issues/2753) [FEATURE] Harvester Cloud Provider compatibility check enhancement

  
## Category: 
* Rancher Integration

## Verification Steps
1. Open Rancher Global settings
1. Edit the `rke-metadata-config`
1. Change the default url to `https://harvester-dev.oss-cn-hangzhou.aliyuncs.com/Untitled-1.json` which include the following cloud provider and csi-driver chart changes
    ```
    "charts": {
        "harvester-cloud-provider": {
        "repo": "rancher-rke2-charts",
        "version": "1.1.0"
        },
        "harvester-csi-driver": {
        "repo": "rancher-rke2-charts",
        "version": "1.1.0"
        },
    ```
1. Save and reload page
1. Open the create RKE2 cluster page 
1. Select the incomparable RKE2 version 
1. Check the Cloud provider drop down 
1. Enable Harvester API in Preference -> Enable Developer Tools & Features
1. Open settings 
1. Click view API of any setting
1. Click up
1. open the  id": "harvester-csi-ccm-versions"
1. Or directly access https://192.168.122.162/v1/harvester/harvesterhci.io.settings/harvester-csi-ccm-versions 
1. Click Edit button
1. Change the default value to `{"harvester-cloud-provider":">=0.0.1 <0.1.2","harvester-csi-provider":">=0.0.1 <0.1.2"}` 
    ![image](https://user-images.githubusercontent.com/29251855/193208619-fd35fc50-9cff-433a-8f7f-ef59420031d6.png)
1. Show and Send request 
1. Repeat step 5 - 7 

## Expected Results
1. When we change the cloud provider and csi-driver chart version in Rancher `rke-metadata-config` setting,
Then we select the incompatibility RKE2 version, the Harvester cloud provider is `disabled` and there will be a warning banner
    ![image](https://user-images.githubusercontent.com/29251855/193209810-214210ae-59ad-438f-bed3-d1ba1ae07cab.png)

1. When we change the cloud provider and csi-driver chart version in Harvester `csi-ccm-versions` according to  [Semver](https://www.npmjs.com/package/semver) expression
Then we select the incompatibility RKE2 versions, the Harvester cloud provider is `disabled` and there will be a warning banner
    ![image](https://user-images.githubusercontent.com/29251855/193209926-5ed58f92-d1f2-4274-b147-919ea82362b0.png)