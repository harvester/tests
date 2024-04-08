---
title: PCI Devices Controller
---

## Pre-requisite Enable PCI devices

1. Create a harvester cluster in bare metal mode. Ensure one of the nodes has NIC separate from the management NIC
1. Go to the management interface of the new cluster
1. Go to Advanced -> PCI Devices
1. Validate that the PCI devices aren't enabled
1. Click the link to enable PCI devices
1. Enable PCI devices in the linked addon page
1. Wait for the status to change to Deploy successful
1. Navigate to the PCI devices page
1. Validate that the PCI devices page is populated/populating with PCI devices


## Case 1 (PCI NIC passthrough)
1. Create a harvester cluster in bare metal mode. Ensure one of the nodes has NIC separate from the management NIC
1. Go to the management interface of the new cluster
1. Go to Advanced -> PCI Devices
1. Check the box representing the PCI NIC device (identify it by the Description or the VendorId/DeviceId combination)
1. Click Enable Passthrough
1. When the NIC device is in an Enabled state, create a VM
1. After creating the VM, edit the Config
1. In the "PCI Devices" section, click the "Available PCI Devices" dropdown
1. Select the PCI NIC device that has been enabled for passthrough
1. Click Save
1. Start the VM
1. Once the VM is booted, run `lspci` at the command line (make sure the VM has the `pciutils` package) and verify that the PCI NIC device shows up
1. (Optional) Install the driver for your PCI NIC device (if it hasn't been autoloaded)

### Case 1 dependencies:
- PCI NIC separate from management network
- Enable PCI devices

## Case 2 (GPU passthrough)

### Case 2-1 Add GPU
1. Create a harvester cluster in bare metal mode. Ensure one of the nodes has a GPU separate from the management NIC
1. Go to the management interface of the new cluster
1. Go to Advanced -> PCI Devices
1. Check the box representing the GPU device (identify it by the Description or the VendorId/DeviceId combination)
1. Click Enable Passthrough
1. When the GPU device is in an Enabled state, create a VM
1. After creating the VM, edit the Config
1. In the "PCI Devices" section, click the "Available PCI Devices" dropdown
1. Select the GPU device that has been enabled for passthrough
1. Click Save
1. Start the VM
1. Once the VM is booted, run `lspci` at the command line (make sure the VM has the `pciutils` package) and verify that the GPU device shows up
1. Install the driver for your GPU device
     1. if the device is from NVIDIA: (this is for ubuntu, but the opensuse installation instructions are [here](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#suse-installation))
        ```
        wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
        sudo dpkg -i cuda-keyring_1.1-1_all.deb
        sudo apt-get update
        sudo apt-get -y install cuda nvidia-cuda-toolkit build-essential

        ```
         1. Check out https://github.com/nvidia/cuda-samples
            `git clone https://github.com/nvidia/cuda-samples`
         1. `cd cuda-samples/Samples/3_CUDA_Features/cudaTensorCoreGemm`
         1. `make`
         1. If you need to install the drivers for the nvidia card you can use the following
            - `sudo apt-get -y install ubuntu-drivers-common && sudo ubuntu-drivers autoinstall`
            - If that doesn't work you might check for drivers that are available with `ubuntu-drivers-common`
         1. Run `./cudaTensorCoreGemm` and verify that the program completed correctly
     1. if the device is from AMD/ATI, install and use the `aticonfig` command to inspect the device

### Case 2-2 Negative add GPU
- **Pre-requisite**: the GPU should already be assigned to another VM
1. On the VM that doesn't have the GPU assigned edit the VM
1. Open up the `PCI Devices` Section
1. Verify that you can't add the already assigned GPU to the VM. It should be greyed out.

### Case 2-3 Remove GPU
1. Edit the VM where the GPU is assigned
1. In the "PCI Devices" section, Clear the available devices
1. Click save
    - If the VM is on then you will be prompted to reboot.
1. Validate that the GPU is removed by using `lspci` and trying to run `dmmaTensorCoreGemm` if the GPU supported CUDA
1. Open up another VM and verify that the GPU is listed as available in the `PCI Devices` section