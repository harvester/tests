---
title: Edit vm config after Eject CDROM and delete volume
---

* Related issues: [#5264](https://github.com/harvester/harvester/issues/5264) [BUG] After EjectCD from vm and edit config of vm displays empty page: "Cannot read properties of null"

## Category: 
* Virtual Machines

## Verification Steps
1. Upload the ISO type desktop image (e.g ubuntu-20.04.4-desktop-amd64.iso)
1. Create a vm named `vm1` with the iso image
1. Open the web console to check content
1. Click EjectCD after vm running
1. Select the `delete volume` option
1. Wait until vm restart to running
1. Click the edit config
1. Back to the virtual machine page
1. Click the `vm1` name 

## Expected Results
* Check can edit vm config of `vm1` to display all settings correctly
{{< image "images/virtual-machines/5264-edit-vm-cofig-after-delete-volume.png" >}}
* Check can display the current `vm1` settings correctly 
