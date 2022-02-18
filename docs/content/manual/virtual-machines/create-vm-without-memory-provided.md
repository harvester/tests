---
title: Create VM without memory provided
---

* Related issues: [#1477](https://github.com/harvester/harvester/issues/1477) intimidating error message when missing mandatory field

## Category: 
* Virtual Machine

## Verification Steps
1. Create some image and volume
1. Create virtual machine
1. Fill out all mandatory field but leave memory blank.
1. Click create 

## Expected Results
Leave empty memory field empty when create virtual machine will show "Memory is required" error message

![image](https://user-images.githubusercontent.com/29251855/140006054-92b12a07-af8b-4087-9fc8-4cf76c6500ea.png)

