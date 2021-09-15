#!/bin/bash

set -e

USAGE="${0}: <version> 

Where:
  <version>: Latest version of terraform provider for Havester 
"

if [ $# -ne 1 ] ; then
        echo "$USAGE"
        exit 1
fi

VER=$1
ARCH=linux_amd64
WGET="wget https://github.com/harvester/terraform-provider-harvester/releases/download/v${VER}/terraform-provider-harvester-amd64.tar.gz"

TERDIR="$PWD/terraform_test_artifacts"
#pushd "$PWD"/terraform_test_artifacts/
pushd "$TERDIR"
`$WGET`
## extract archive
tar -zxvf ./terraform-provider-harvester-amd64.tar.gz
terraform_harvester_provider_bin=${TERDIR}/terraform-provider-harvester

terraform_harvester_provider_dir="${TERDIR}/.terraform.d/plugins/registry.terraform.io/harvester/harvester/${VER}/${ARCH}/"
mkdir -p "${terraform_harvester_provider_dir}"
cp ${terraform_harvester_provider_bin} "${terraform_harvester_provider_dir}/terraform-provider-harvester_v${VER}"

TFRCFILE="dev.tfrc"
if [ -e $TFRCFILE ]; then
  echo "File $TFRCFILE already exists!"
else
  cat > $TFRCFILE <<EOF
provider_installation {
  dev_overrides {
    "registry.terraform.io/harvester/harvester" = "${terraform_harvester_provider_dir}"
  }
}
EOF
fi

rm -rf ${TERDIR}/install-terraform-provider-harvester.sh
rm -rf ${TERDIR}/terraform-provider-harvester-amd64.tar.gz
rm -rf ${TERDIR}/terraform-provider-harvester

popd
