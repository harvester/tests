---
title: CPU overcommit on VM (e2e_fe)
---
Ref: <https://github.com/harvester/harvester/issues/1429>

## Verify Items

- Overcommit can be edit on Dashboard
- VM can allocate exceed CPU on the host Node
- VM can chage allocated CPU after created

## Case: Update Overcommit configuration

1. Install Harvester with any Node
1. Login to Dashboard, then navigate to **Advanced Settings**
1. Edit `overcommit-config`
1. The field of **CPU** should be editable
1. Created VM can allocate maximum CPU should be `<HostCPUs> * [<overcommit-CPU>/100] - <Host Reserved>`

## Case: VM can allocate CPUs more than Host have

1. Install Harvester with any Node
1. Create a cloud image for VM Creation
1. Create a VM with `<HostCPUs> * 5` CPUs
1. VM should start successfully
1. `lscpu` in VM should display allocated CPUs
1. Page of Virtual Machines should display allocated CPUs correctly

## Case: Update VM allocated CPUs

1. Install Harvester with any Node
1. Create a cloud image for VM Creation
1. Create a VM with `<HostCPUs> * 5` CPUs
1. VM should start successfully
1. Increase/Reduce VM allocated CPUs to minimum/maximum
1. VM should start successfully
1. `lscpu` in VM should display allocated CPUs
1. Page of Virtual Machines should display allocated CPUs correctly
