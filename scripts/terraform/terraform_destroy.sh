#!/bin/bash

set -e

TMPDIR="/tmp/terraformharvester"

# Check if temp dir exists 
if [ ! -d $TMPDIR ]; then
    >&2 echo "temp directory doesn't exist"
    exit 1
fi

# Make sure it gets removed even if the script exits abnormally.
trap "exit 1"           HUP INT PIPE QUIT TERM
trap 'rm -rf "$TMPDIR"' EXIT

pushd "$TMPDIR" 
terraform destroy -auto-approve
popd
