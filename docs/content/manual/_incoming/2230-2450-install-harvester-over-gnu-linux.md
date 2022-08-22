---
title: Install Harvester over previous GNU/Linux install
---

* Related issues: [#2230](https://github.com/harvester/harvester/issues/2230) [BUG] harvester installer - always first attempt failed if before was linux installed
* Related issues: [#2450](https://github.com/harvester/harvester/issues/2450) [backport v1.0][BUG] harvester installer - always first attempt failed if before was linux installed #2450


## Category: 
* Installtion

## Verification Steps

1. Install GNU/LInux LVM configuration
1. reboot
1. Install Harvester via ISO over previous linux install
1. Verifiy Harvester install by changing password and logging in.

## Expected Results
1. Install should complete