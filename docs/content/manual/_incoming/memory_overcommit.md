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
2. Login to Dashboard, then navigate to **Advanced Settings**
3. Edit `overcommit-config`
4. The field of **Memory** should be editable
5. Created VM can allocate maximum Memory should be `<HostMemory> * [<overcommit-Memory>/100] - <Host Reserved>`

## Case: VM can allocate Memory more than Host have
1. Install Harvester with any Node
2. Create a cloud image for VM Creation
3. Create a VM with `<HostMemory> * 1.2` Memory
4. VM should start successfully
5. `lscpu` in VM should display allocated Memory
6. Page of Virtual Machines should display allocated Memory correctly

## Case: Update VM allocated Memory
1. Install Harvester with any Node
2. Create a cloud image for VM Creation
3. Create a VM with `<HostMemory> * 1.2` Memory
4. VM should start successfully
5. Increase/Reduce VM allocated Memory to minimum/maximum
6. VM should start successfully
7. `lscpu` in VM should display allocated Memory
8. Page of Virtual Machines should display allocated Memory correctly
