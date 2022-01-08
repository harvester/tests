---
title: Verify that vm-force-reset-policy works
---

* Related issues: [#1660](https://github.com/harvester/harvester/issues/1660) The volume unit on the vm details page is incorrect

## Verification Steps
1. Create new .1G volume
1. Create new VM
1. Create with raw-image template
1. Add opensuse base image
1. Add .1G Volume
1. Verify size in VM details on volume tab
![image](https://user-images.githubusercontent.com/83787952/145658516-73f5c72c-2543-46cd-9f90-8bc47f5ce2d4.png)

## Expected Results
1. Size should show as .1G