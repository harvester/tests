---
title: Create multiple VM instances using VM template with EFI mode selected
---

* Related issues: [#2577](https://github.com/harvester/harvester/issues/2577) [BUG] Boot in EFI mode not selected when creating multiple VM instances using VM template with EFI mode selected.

## Category: 
* Virtual Machine

## Verification Steps
1. Create a VM template, check the `Booting in EFI mode`
1. Wait for all VM running
1. Check the EFI mode is enabled in VM config
1. ssh to each VM
1. Check the /etc/firmware/efi file
   
## Expected Results
Can create multiple VM instance using VM template with EFI mode selected

* All VMs are running
![image](https://user-images.githubusercontent.com/29251855/182343361-532a7cee-04de-4a0e-9bc6-803f7cc66e94.png)

* Check VM setting, the booting in EFI mode is checked
![image](https://user-images.githubusercontent.com/29251855/182343254-4a421a04-aa3f-471c-a258-930a98cc84d3.png)

* Access each VM we can see `/sys/firmware/efi` present
  ```
  ubuntu@efi-01:~$ ls /sys/firmware/
  acpi  dmi  efi  memmap
  ```
  ```
  ubuntu@efi-02:~$ ls /sys/firmware/
  acpi  dmi  efi  memmap
  ```
  ```
  ubuntu@efi-03:~$ ls /sys/firmware
  acpi  dmi  efi  memmap
  ```