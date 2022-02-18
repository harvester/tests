---
title: Memory overcommit on VM
---
Ref: https://github.com/harvester/harvester/issues/1537

## Verify Items
  - Overcommit can be edit on Dashboard
  - VM can allocate exceed Memory on the host Node
  - VM can chage allocated Memory after created

## Case: Update Overcommit configuration
1. Install Harvester with any Node
1. Login to Dashboard, then navigate to **Advanced Settings**
1. Edit `overcommit-config`
1. The field of **Memory** should be editable
1. Created VM can allocate maximum Memory should be `<HostMemory> * [<overcommit-Memory>/100] - <Host Reserved>`

## Case: VM can allocate Memory more than Host have
1. Install Harvester with any Node
1. Create a cloud image for VM Creation
1. Create a VM with `<HostMemory> * 1.2` Memory
1. VM should start successfully
1. `lscpu` in VM should display allocated Memory
1. Page of Virtual Machines should display allocated Memory correctly

## Case: Update VM allocated Memory
1. Install Harvester with any Node
1. Create a cloud image for VM Creation
1. Create a VM with `<HostMemory> * 1.2` Memory
1. VM should start successfully
1. Increase/Reduce VM allocated Memory to minimum/maximum
1. VM should start successfully
1. `lscpu` in VM should display allocated Memory
1. Page of Virtual Machines should display allocated Memory correctly
