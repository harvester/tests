---
title: Project owner role on customized project open Harvester cluster  
---

* Related issues: [#2394](https://github.com/harvester/harvester/issues/2394) [BUG] Standard rancher user with project owner role of customized project to access Harvester get "404 Not Found" error
* Related issues: [#2395](https://github.com/harvester/harvester/issues/2395) [backport v1.0] [BUG] Standard rancher user with project owner role of customized project to access Harvester get "404 Not Found" error

## Category: 
* Rancher integration

## Verification Steps
1. Import Harvester from Rancher
1. Access Harvester on virtualization management page
1. Create a project test and namespace test under it
1. Go to user authentication page
1. Create a stand rancher user test
1. Access Harvester in Rancher
1. Set project owner role of test project to test user
1. Login Rancher with test user
1. Access the virtualization management page

## Expected Results
* Now the standard user with project owner role can access harvester in virtualization management page correctly
![image](https://user-images.githubusercontent.com/29251855/174706597-f98ecc41-b479-4e5b-b163-02f43c1c6138.png)

