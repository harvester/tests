#!/bin/bash

set -e

#check to clean only dir_only or all (dir + resource)
if [ $# -ne 1 ]; then
    DESTROYTYPE="all"
else
    DESTROYTYPE="$1"
fi

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
trap 'rm -rf "$TMPDIR" "$KUBEDIR" ' EXIT

pushd "$TMPDIR"

#Remove resource for destroytype all
if [[ "$DESTROYTYPE" == "all" ]] ; then
  "$TERDIR"/bin/terraform destroy -auto-approve
else
  "$TERDIR"/bin/terraform destroy -auto-approve --target $DESTROYTYPE
fi
popd