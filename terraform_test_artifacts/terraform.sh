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

TERDIR="$PWD"/terraform_test_artifacts
mv "$TERDIR"/resource* "$TMPDIR"
mv -f "$TERDIR"/provider.tf "$TMPDIR"

pushd "$TMPDIR" 
#terraform init
TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform plan -out tfplan -input=false 
TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform apply -input=false tfplan 
popd
