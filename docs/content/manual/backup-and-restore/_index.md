---
title: Backup and Restore
---
All backup tests should be ran against both S3 and NFS backup targets

- In user data mention the below to access the vm
    - 
    ```
    # cloud-config
    password: password
    chpasswd: {expire: False}
    sshpwauth: True
    ```
- Cloud images
    - Ubuntu: https://cloud-images.ubuntu.com/releases/  (default user: ubuntu)
        - v0.3.0 tested: https://cloud-images.ubuntu.com/releases/focal/release/
    - openSUSE: http://download.opensuse.org/repositories/Cloud:/Images:/(default user: opensuse)
        - v0.3.0 tested: http://download.opensuse.org/repositories/Cloud:/Images:/    Leap_15.3/images/
    - Windows: N/A
- Script for quickly creating files
    - 
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