---
title: Project owner should not see additional alert
---

* Related issues: [#2288](https://github.com/harvester/harvester/issues/2288) [BUG] The project-owner user will see an additional alert
* * Related issues: [#2350](https://github.com/harvester/harvester/issues/2350) [Backport v1.0] The project-owner user will see an additional alert

## Category: 
* Rancher integration

## Verification Steps
1. Importing a harvester cluster in a rancher cluster
1. enter the imported harvester cluster from the `Virtualization Management` page
1. create a new Project  (test), Create a test namespace in the test project.
1. go to `Network` page, add `vlan 1`
1. create a vm，  choose  `test namespace`,  choose `vlan network`, click save
1. create a new user (test),  choose `Standard User`
1. go to the `project page`, edit `test` Project, set `test` user to Project Owner。
<img width="1543" alt="image" src="https://user-images.githubusercontent.com/24985926/169200683-2532871a-980e-43b2-ae76-87b1d44f5a35.png">
1. login again with `test user`
1. go to the vm page

## Expected Results
* Use rancher standard user `test` with project owner permission to access Harvester.
Now there is no error alert on the created VM with vlan1 network 
![image](https://user-images.githubusercontent.com/29251855/174733151-c8bcffdd-50e0-404e-a5b6-a9ff2f1a7387.png)
