---
title: Generate Install Support Config Bundle For Single Node
---

 * Related issue: [#1864](https://github.com/harvester/harvester/issues/1864)  Support bundle for a single node (Live/Installed)

 * Related issue: [#272](https://github.com/harvester/harvester-installer/pull/272)  Generate supportconfig for failed installations

## Category: 
* Support

## Environment setup
Setup a single node harvester from ISO install but don't complete the installation
1. Gain SSH Access to the Single Harvester Node
1. Once Shelled into the Single Harvester Node edit the `/usr/sbin/harv-install`
1. Using: [harvester-installer's harv-install as a reference](https://github.com/harvester/harvester-installer/blob/master/package/harvester-os/files/usr/sbin/harv-install#L362) edit around line #362 adding `exit 1`:
```
exit 1
trap cleanup exit
check_iso
```
save the file.
1. Continue to configure the node, when asked to Optionally provide a Harvester Configuration URL, do so and have the `config.yaml` have debug enabled on install like:
```
install:
  debug: true
```

## Verification Steps
1. SCP the *.txz file provided at the path shown in ISO install something like: /var/log/__.txz from your Single Harvester Node to your remote machine
1. Untar `tar xvf` the *.txz file 

## Expected Results
1. Install should fail - reference ![image](https://user-images.githubusercontent.com/5370752/165647594-b3529472-e606-4d12-8953-54ff5d86c00e.png)
1. Install should generate a support config with a similar directory structure to: ![image](https://user-images.githubusercontent.com/5370752/165647582-d487b4ec-dcf1-451d-a063-6502ebd97012.png) - you can examine the files
