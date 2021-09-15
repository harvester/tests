#!/bin/bash

set -e

TMPDIR="$PWD"/terraform_test_artifacts/terraformharvester
KUBEDIR="$PWD"/terraform_test_artifacts/.kube
TERDIR="$PWD"/terraform_test_artifacts
# Check if temp dir exists 
if [ ! -d $TMPDIR ]; then
    >&2 echo "temp directory doesn't exist"
    exit 1
fi

# Make sure it gets removed even if the script exits abnormally.
trap "exit 1"           HUP INT PIPE QUIT TERM
trap 'rm -rf "$TMPDIR" "$KUBEDIR"' EXIT

pushd "$TMPDIR" 
TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform destroy -auto-approve
popd
