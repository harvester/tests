#!/bin/bash
# first file
if [ $1 = 1 ]
then
    dd if=/dev/urandom of=file1.txt count=10 bs=1M
    md5sum file1.txt > file1.md5
#    md5sum -c file1.md5
fi
## overwrite file1 and create file2
if [ $1 = 2 ]
then
    dd if=/dev/urandom of=file1.txt count=10 bs=1M
    dd if=/dev/urandom of=file2.txt count=10 bs=1M
    md5sum file1.txt > file1-2.md5
    md5sum file2.txt > file2.md5
#    md5sum -c file1.md5 file1-2.md5 file2.md5
fi
## overwrite file2 and create file3
if [ $1 = 3 ]
then
    dd if=/dev/urandom of=file2.txt count=10 bs=1M
    dd if=/dev/urandom of=file3.txt count=10 bs=1M
    md5sum file2.txt > file2-2.md5
    md5sum file3.txt > file3.md5
#    md5sum -c file2.md5 file1-2.md5 file2-2.md5 file3.md5
fi
