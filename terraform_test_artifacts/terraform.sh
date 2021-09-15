#!/bin/bash

set -e

# Make a temporary folder
TMPDIR="$PWD"/terraform_test_artifacts/terraformharvester
mkdir -p "$TMPDIR"

# Check if temp dir is  created successfully.
if [ ! -e $TMPDIR ]; then
    >&2 echo "Failed to create temp directory"
    exit 1
fi

mv "$PWD"/terraform_test_artifacts/resource* "$TMPDIR"
mv -f "$PWD"/terraform_test_artifacts/provider.tf "$TMPDIR"

pushd "$TMPDIR" 
terraform init
terraform plan -out tfplan -input=false 
terraform apply -input=false tfplan 
popd
