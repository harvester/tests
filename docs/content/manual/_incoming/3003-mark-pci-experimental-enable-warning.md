---
title: Mark pcidevices-controller add-on as experimental and add warning when enable devices
---

* Related issues: [#3003](https://github.com/harvester/harvester/issues/3003) [FEATURE] Mark pcidevices-controller add-on as experimental and add warning when enable devices
  
## Category: 
* PCI-Devices

## Verification Steps
1. Go to the Addons page 
1. Enable the `pcidevices-controller` 
![image](https://user-images.githubusercontent.com/29251855/197666189-dc70fe3e-21dc-4a38-8262-b16e23f10907.png)
![image](https://user-images.githubusercontent.com/29251855/197666231-01f16d2e-2db3-429b-b0d5-a37ccc2e8586.png)
1. Go to PCI Devices page
1. Wait for the detection complete
1. Change to group view
1. Enable the Gigabit Network Connection
![image](https://user-images.githubusercontent.com/29251855/197666706-9e9bb6e3-928a-4e29-8175-76268e60599e.png)
1. Enable any group of devices


## Expected Results
1.  In Addons page, the `pcidevices-controller` config is named with `(Experimental)` 
![image](https://user-images.githubusercontent.com/29251855/197665632-acdb3fb5-376d-4cb4-add9-89fcf535543f.png)
![image](https://user-images.githubusercontent.com/29251855/197665870-0ea74790-4669-4710-acee-653e0cabb3da.png)
1. When we enable the the Gigabit Network Connection, there will be a prompt dialog to warn the user to ensure enabling the current device would not cause damage to the cluster
![image](https://user-images.githubusercontent.com/29251855/197667282-6b938d96-4070-4aab-a680-c38ca7a28dc7.png)
1. When we enable a group of devices, there will also prompt the warning dialog 
![image](https://user-images.githubusercontent.com/29251855/197668951-bd34b22a-bffd-4db2-abb2-aba0e02b4f6e.png)

