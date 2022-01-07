---
title: Delete the image	(e2e_be)
---
1. Select an image with state active.
1. Delete the image.
1. Create another image with same name.
1. Delete the newly created image.
1. Delete an image with failed state

## Expected Results
1. The image should be deleted successfully. Check the CRDS VirtualMachineImage.
1. User should be able to create a new image with same name.
1. Check the backing image in Longhorn.
