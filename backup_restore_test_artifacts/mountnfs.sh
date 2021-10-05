#!/bin/bash

set -e

USAGE="${0}: <nfs-endpoint>

Where:

  <nfs endpoint>: endpoint for remote nfs share 
"

if [ $# -ne 1 ] ; then
        echo "$USAGE"
        exit 1
fi

NFSENDPOINT=$1

TMPDIR="$PWD"/backup_restore_test_artifacts/nfsshare
mkdir -p "$TMPDIR"
# Check if temp dir is  created successfully.
if [ ! -e $TMPDIR ]; then
    >&2 echo "Failed to create temp directory"
    exit 1
fi

pushd "$TMPDIR" > /dev/null 
sudo mount -t nfs4 -o nfsvers=4.2 "$NFSENDPOINT" "$PWD" 
sudo chown -R $(whoami) $TMPDIR
cd "$TMPDIR"
out=$(ls -R | wc -l)
echo "$out"
popd > /dev/null

sudo umount "$TMPDIR"
rm -rf "$TMPDIR"

