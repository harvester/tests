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

"$TERDIR"/bin/terraform init
if [ $1 == "import" ]; then
   "$TERDIR"/bin/terraform import harvester_clusternetwork.vlan harvester-system/vlan
fi

"$TERDIR"/bin/terraform plan -out tfplan -input=false
"$TERDIR"/bin/terraform apply -input=false tfplan
popd