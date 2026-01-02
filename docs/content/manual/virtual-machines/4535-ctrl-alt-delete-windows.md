---
title: Click ctrl-alt-delete in Windows 
---

* Related issues: [#4535](https://github.com/harvester/harvester/issues/4535) [BUG] Sending ctrl-alt-delete does not have any reaction on a windows VM

## Category: 
* Virtual Machines

## Verification Steps
1. Create windows server 2022 iso image
1. Create a VM, add the second SATA disk
1. Install windows server 2022 with desktop
1. After installation complete
1. Open the web console
1. In the windows login page, click the Shortcut Keys then click Ctrl , Alt, Del in sequence
1. After login to desktop
1. Click Ctrl , Alt, Del in sequence again

## Expected Results
* Click ctrl+alt+delete key combination works on windows login page

* Click ctrl+alt+delete key combination works inside windows
