---
title: Press the Enter key in setting field shouldn't refresh page
---

* Related issues: [#2569](https://github.com/harvester/harvester/issues/2569) [BUG] Press the Enter key, the page will be refreshed automatically

## Category: 
* Settings

## Verification Steps
1. Check every page have input filed in the Settings page
1. Move cursor to any input field 
1. Click the `Enter` button 
1. Check the page will not be automatically loaded



## Expected Results
On v1.0.3 backport, when we press the `Enter` key in the following page fields, it will not being refreshed automatically.

Also checked the following pages

* http proxy
* overcommit-config
* support-bundle-image
* vm-force-reset-policy
* backup target
* release download url
* Cluster registration 
* ui-index
* upgrade-checker-url
* support-bundle-timeout

