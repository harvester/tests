---
title: Update image labels after deleting source VM(e2e_fe)
---

* Related issues: [#1602](https://github.com/harvester/harvester/issues/1602) exported image can't be deleted after vm removed

## Verification Steps
1. create vm "vm-1"
1. create a image "img-1" by export the volume used by vm "vm-1"
1. delete vm "vm-1"
1. update image "img-1" labels

## Expected Results
1. image "img-1" will be updated