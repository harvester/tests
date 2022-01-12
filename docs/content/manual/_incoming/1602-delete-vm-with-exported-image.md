---
title: Delete VM with exported image
---

* Related issues: [#1602](https://github.com/harvester/harvester/issues/1602) exported image can't be deleted after vm removed

## Verification Steps
1. create vm "vm-1"
1. create a image "img-1" by export the volume used by vm "vm-1"
1. delete vm "vm-1"
1. delete image "img-1"

## Expected Results
1. image "img-1" will be deleted