---
title: Boot installer under Legacy BIOS and UEFI
---
* Related issues [#2023](https://github.com/harvester/harvester/issues/2023) Legacy Iso for older servers

## Verification Steps

### BIOS Test
1. Build [harvester-installer](https://github.com/harvester/harvester-installer)
1. Boot build artifact using BIOS Legacy mode: `qemu-system-x86_64 -m 2048 -cdrom ../dist/artifacts/harvester-master-amd64`
1. Verify that the installer boot process reaches the screen that says "Create New Cluster" or "Join existing cluster"

### UEFI Test
1. Build [harvester-installer](https://github.com/harvester/harvester-installer) (or use the same one from the BIOS Test, it's a hybrid ISO)
1. Boot build artifact using UEFI mode: `qemu-system-x86_64 -m 2048 -cdrom ../dist/artifacts/harvester-master-amd64 -bios /usr/share/qemu/ovmf-x86_64.bin` (OVMF is a port of the UEFI firmware to qemu)
1. Verify that the installer boot process reaches the screen that says "Create New Cluster" or "Join existing cluster"
