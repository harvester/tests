---
title: allow users to create cloud-config template on the VM creating page
---

* Related issues: [#1433](https://github.com/harvester/harvester/issues/1433) allow users to create cloud-config template on the VM creating page

## Category: 
* Virtual Machine

## Verification Steps
1. Create a new virtual machine
1. Click advanced options
1. Drop down user data template -> create new
1. Drop down network data template -> create new

## Expected Results
1. User can create user and network data template when create virtual machine
![image](https://user-images.githubusercontent.com/29251855/139009117-9c191986-2253-4bff-b73f-962eabe2b2d9.png)
Created cloud-init template 
1. template can be saved and auto selected to the latest one
![image](https://user-images.githubusercontent.com/29251855/139008946-97f0d528-c5b9-4add-82d9-4105bd51f0c5.png)



