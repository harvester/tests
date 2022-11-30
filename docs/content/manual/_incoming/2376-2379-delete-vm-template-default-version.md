---
title: Delete VM template default version (e2e_fe)
---

* Related issues: [#2376](https://github.com/harvester/harvester/issues/2376) [BUG] Cannot delete Template
* Related issues: [#2379](https://github.com/harvester/harvester/issues/2379) [backport v1.0.3] Cannot delete Template

## Category: 
* VM Template

## Verification Steps
1. Go to Advanced -> Templates
1. Create a new template
1. Modify the template to create a new version
1. Click the config button of the `default version` template
1. Click the config button of the `non default version` template

## Expected Results
* If the template is the `default version`, it will not display the `delete` button 
  ![image](https://user-images.githubusercontent.com/29251855/174030567-b2c6ae52-40d1-4dd6-9ede-783409bd3c87.png)

* If the template is **not** the `default version`, it will display the `delete` button 
  ![image](https://user-images.githubusercontent.com/29251855/174030720-5fb040e0-73f8-4697-8b0f-ee02d407b5d4.png)

* We can also delete the entire template from the config button
  ![image](https://user-images.githubusercontent.com/29251855/174030849-5f4ed7c8-1351-4b13-b3ca-d377b5b4f6c0.png)


