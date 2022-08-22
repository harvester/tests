---
title: template with EFI
---

* Related issues: [#2577](https://github.com/harvester/harvester/issues/2577) [BUG] Boot in EFI mode not selected when creating multiple VM instances using VM template with EFI mode selected.

## Category: 
* Template

## Verification Steps
1. Go to Template, create a VM template with Boot in EFI mode selected. 
![image](https://user-images.githubusercontent.com/9990804/181196319-d95a4d23-ea31-418c-9fd2-152821d56930.png)
1. Go to Virtual Machines, click Create, select Multiple instance, type in a random name prefix, and select the VM template we just created.
![image](image.png)
1. Go to Advanced Options, for now this EFI checkbox should be checked without any issue.
![image](https://user-images.githubusercontent.com/9990804/181196934-1249902f-47dd-44dc-bced-5911ffcfdf16.png)
1. Create a VM with template
## Expected Results
1. Check VM setting, the booting in EFI mode is checked
![image](https://user-images.githubusercontent.com/29251855/182343254-4a421a04-aa3f-471c-a258-930a98cc84d3.png)
1. Verify that VM is running with UEFI using 
```
ubuntu@efi-01:~$ ls /sys/firmware/
acpi  dmi  efi  memmap

```