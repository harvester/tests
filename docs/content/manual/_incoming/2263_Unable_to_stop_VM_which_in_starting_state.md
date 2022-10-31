---
title: Unable to stop VM which in starting state
category: UI
tags: VM, p2, acceptance
---
Ref: https://github.com/harvester/harvester/issues/2263


### Verify Steps:
1. Install Harvester with any nodes
1. Create an Windows iso image for VM creation
1. Create the Windows VM by using the iso image
1. When the VM in **Starting** state, **Stop** button should able to click and work as expected