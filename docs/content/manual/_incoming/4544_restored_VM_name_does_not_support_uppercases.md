---
title: Restored VM name does not support uppercases
---
* Related issues: [#4544](https://github.com/harvester/harvester/issues/4544) [BUG] Unable to restore backup into new VM when the name starts with upper case


## Category: 
* Backup/Restore


## Verification Steps
1. Setup `backup-target` in 'Advanced' -> 'Settings'
1. Create an image for VM creation
1. Create a VM `vm1`
1. Take a VM backup `vm1b`
1. Go to 'Backup & Snapshot', restore `vm1b` to new VM

### Positive Cases
1. Single lower
1. Lowers
1. Lowers contains '.'
1. Lowers contains '-'
1. Lowers contains '.' and '-'
![image](https://user-images.githubusercontent.com/2773781/270225975-17fea11e-a266-484d-a9d4-3e3af1624d45.png)


### Negtive Cases
1. Upper
![image](https://github.com/harvester/harvester/assets/2773781/b2411e02-e0c1-4fef-b996-997c8c827862)

1. Upper infront of valid
![image](https://github.com/harvester/harvester/assets/2773781/15f47599-19d8-470e-8c1a-bea7e9c3a28b)

1. Upper append to valid
![image](https://github.com/harvester/harvester/assets/2773781/cbb30195-1abe-47fd-be9c-0938145e1d85)

1. Upper in the middle of valid
![image](https://github.com/harvester/harvester/assets/2773781/26737717-6f71-4707-8042-a7a05de0858e)


## Expected Results
VM name should comply with following rules:
* lower alphanumeric characters, '-' or '.'
* start and end with an alphanumeric character