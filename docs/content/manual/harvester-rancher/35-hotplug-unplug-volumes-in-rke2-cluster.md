---
title: 35-Hot plug and unplug volumes in RKE2 cluster
---
Prerequisite:
Already provisioned RKE2 cluster machine on Harvester

1. Open RKE2 harvester from hamburger menu
2. Open Storage
3. Select `PersistentVolumes`
4. Click Create
5. Provide `Name`
6. Select volume plugin to `Local`
7. Open `Custom`
8. Select `harvester` in `Assign to Storage Class`
![image](https://user-images.githubusercontent.com/29251855/141814258-7f118d6c-45da-40c5-8d9c-a9c3830d4862.png)
9.  Click create


## Expected Results
1. Can create persistent volume correctly
2. Can remove persistent volume correctly