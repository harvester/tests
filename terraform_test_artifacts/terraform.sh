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

#Check whether we need to Import clusternetwork vlan
if [ $# -ne 1 ]; then
   IMPYESNO="no"
   RESEXIST=1
else 
   RESEXIST=$(grep 'harvester_clusternetwork' "${TERDIR}/terraformharvester/terraform.tfstate" | wc -l )
   IMPYESNO="$1"
fi

pushd "$TMPDIR" 
echo "$RESEXIST"
if [ "$RESEXIST" -eq 0 ]; then
   IMPYESNO="$1"
else
   IMPYESNO="no"
fi

#terraform import
if [ "$IMPYESNO" == "import" ]; then
#terraform import
   TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform import harvester_clusternetwork.vlan harvester-system/vlan
fi

#terraform init
TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform plan -out tfplan -input=false 
TF_CLI_CONFIG_FILE="$TERDIR"/dev.tfrc terraform apply -input=false tfplan 
popd
