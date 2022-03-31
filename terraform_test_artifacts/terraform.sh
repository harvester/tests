#!/bin/bash

set -e

# Make a temporary folder
#DATE_WITH_TIME=`date "+%Y%m%d-%H%M%S"`
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
if [ $1 == "cluster" ]; then
   "$TERDIR"/bin/terraform import harvester_clusternetwork.vlan vlan
fi

if [ $1 == "network" ]; then
   "$TERDIR"/bin/terraform import harvester_network.$2 default/$2
fi

"$TERDIR"/bin/terraform plan -out tfplan -input=false
"$TERDIR"/bin/terraform apply -input=false tfplan
popd
