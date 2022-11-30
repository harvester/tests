---
title: Image naming with inline CSS (e2e_fe)
---

* Related issues: [#2563](https://github.com/harvester/harvester/issues/2563) [[BUG] harvesterhci.io.virtualmachineimage spec.displayName displays differently in single view of image

## Category: 
* Images

## Verification Steps
1. Go to images
1. Click "Create"
1. Upload an image or leverage an url - but name the image something like:
`<strong><em>something_interesting</em></strong>`
1. Wait for upload to complete.
1. Observe the display name within the list of images
1. Compare that to clicking into the single image and viewing it 

## Expected Results
1. The list view naming would be the same as the single view of the image