#!/bin/bash

set -e

USAGE="${0}: [<version>] 

Where:
  <version>: version of to dowload. If absent, it will download the latest.
"

ARCH=linux_amd64
DOWNLOAD_URL=
if [ $# -eq 0 ] ; then
	# lookup the latest release download URL
	DOWNLOAD_URL=$(curl https://api.github.com/repos/harvester/terraform-provider-harvester/releases/latest | grep "browser_download_url" | awk '{print $2}' | tr -d '"')
elif [ $# -eq 1 ] ; then
	VER=$1
	DOWNLOAD_URL="https://github.com/harvester/terraform-provider-harvester/releases/download/v${VER}/terraform-provider-harvester-amd64.tar.gz"
else
        echo "$USAGE"
        exit 1
fi

ARCH=linux_amd64

TERDIR="$PWD/terraform_test_artifacts"
if [ -d "$TERDIR"/.terraform.d ]; then
  rm -rf ${TERDIR}/.terraform.d
fi
pushd "$TERDIR"
TFRCFILE="dev.tfrc"
if [ -e $TFRCFILE ]; then
  rm -rf $TFRCFILE
fi

`wget ${DOWNLOAD_URL}`
## extract archive
tar -zxvf ./terraform-provider-harvester-amd64.tar.gz
terraform_harvester_provider_bin=${TERDIR}/terraform-provider-harvester

terraform_harvester_provider_dir="${TERDIR}/.terraform.d/plugins/registry.terraform.io/harvester/harvester/${VER}/${ARCH}/"
mkdir -p "${terraform_harvester_provider_dir}"
cp ${terraform_harvester_provider_bin} "${terraform_harvester_provider_dir}/terraform-provider-harvester_v${VER}"

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

if [ -d "$TERDIR"/.kube ]; then
  rm -rf ${TERDIR}/.kube
fi
if [ -d "$TERDIR"/terraformharvester ]; then
  rm -rf ${TERDIR}/terraformharvester
fi

popd
