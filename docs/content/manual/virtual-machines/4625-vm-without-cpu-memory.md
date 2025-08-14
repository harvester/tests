---
title: VM creation without cpu and memory 
---

* Related issues: [#4625](https://github.com/harvester/harvester/issues/4625) [ENHANCEMENT] Add webhook for CRD virtualmachinetemplateversion.harvesterhci.io


## Category: 
* Virtual Machines

## Verification Steps
1. Create a virtual machine
1. Leave the cpu and memory empty and click create
1. Check the UI message and reaction
1. Leave only cpu or memory empty and click create
1. Check the UI message and reaction
1. Leave the name and image empty and click create
1. Provide all the necessary information to click create
1. Check can create virtual machine correctly

## Expected Results
* Prevent vm creation without input the cpu and memory
{{< image "images/virtual-machines/4625-without-cpu-memory.png" >}}

* Prevent vm creation without input the image and name
{{< image "images/virtual-machines/4625-without-image-name.png" >}}