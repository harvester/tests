#!/bin/bash

set -e

# Make a temporary folder
mkdir -p "/tmp/terraformharvester"
TMPDIR="/tmp/terraformharvester"

# Check if temp dir is  created successfully.
if [ ! -e $TMPDIR ]; then
    >&2 echo "Failed to create temp directory"
    exit 1
fi

mv "$PWD"/scripts/terraform/resource* "$TMPDIR"
cp "$PWD"/scripts/terraform/provider.tf "$TMPDIR"

pushd "$TMPDIR" 
terraform init
terraform plan -out tfplan -input=false 
terraform apply -input=false tfplan 
popd
