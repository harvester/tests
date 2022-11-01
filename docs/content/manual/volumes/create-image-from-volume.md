---
title: Create image from Volume(e2e_fe)
---
1. Create new VM
1. Add SSH key
1. Run through iterations for 1, 2, and 3 for attached bash script
1. Export volume to image from volumes page
1. Create new VM from image
1. Run `md5sum -c file2.md5 file1-2.md5 file2-2.md5 file3.md5`

## Expected Results
1. image should upload/complete in images page
1. New VM should create
1. SSH key should work on new VM
1. file2.md5 should fail and the other three md5 checks should pass

### Comments
```
#!/bin/bash
# first file
if [ $1 = 1 ]
then
    dd if=/dev/urandom of=file1.txt count=100 bs=1M
    md5sum file1.txt > file1.md5
    md5sum -c file1.md5
fi
## overwrite file1 and create file2
if [ $1 = 2 ]
then
    dd if=/dev/urandom of=file1.txt count=100 bs=1M
    dd if=/dev/urandom of=file2.txt count=100 bs=1M
    md5sum file1.txt > file1-2.md5
    md5sum file2.txt > file2.md5
    md5sum -c file1.md5 file1-2.md5 file2.md5
fi
## overwrite file2 and create file3
if [ $1 = 3 ]
then
    dd if=/dev/urandom of=file2.txt count=100 bs=1M
    dd if=/dev/urandom of=file3.txt count=100 bs=1M
    md5sum file2.txt > file2-2.md5
    md5sum file3.txt > file3.md5
    md5sum -c file2.md5 file1-2.md5 file2-2.md5 file3.md5
fi
```