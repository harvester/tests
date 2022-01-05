---
title: CPU overcommit on VM
---
Ref: https://github.com/harvester/harvester/issues/1429

## Verify Items
  - Overcommit can be edit on Dashboard
  - VM can allocate exceed CPU on the host Node
  - VM can chage allocated CPU after created

## Case: Update Overcommit configuration
1. Install Harvester with any Node
2. Login to Dashboard, then navigate to **Advanced Settings**
3. Edit `overcommit-config`
4. The field of **CPU** should be editable
5. Created VM can allocate maximum CPU should be `<HostCPUs> * [<overcommit-CPU>/100] - <Host Reserved>`

## Case: VM can allocate CPUs more than Host have
1. Install Harvester with any Node
2. Create a cloud image for VM Creation
3. Create a VM with `<HostCPUs> * 5` CPUs
4. VM should start successfully
5. `lscpu` in VM should display allocated CPUs
6. Page of Virtual Machines should display allocated CPUs correctly

## Case: Update VM allocated CPUs
1. Install Harvester with any Node
2. Create a cloud image for VM Creation
3. Create a VM with `<HostCPUs> * 5` CPUs
4. VM should start successfully
5. Increase/Reduce VM allocated CPUs to minimum/maximum
6. VM should start successfully
7. `lscpu` in VM should display allocated CPUs
8. Page of Virtual Machines should display allocated CPUs correctly
