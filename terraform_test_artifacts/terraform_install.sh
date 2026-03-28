#!/bin/bash

set -e

USAGE="${0}: [<version>] [<checksum>]
Where:
  <version>: version of to download. If absent, it will download the last one set.
  <checksum>: SHA256 checksum of the Terraform binary.
"

DOWNLOAD_URL=
if [ $# -eq 0 ] ; then
	# lookup the latest release download URL
    VER=1.14.8
    TERRAFORM_CHECKSUM=56a5d12f47cbc1c6bedb8f5426ae7d5df984d1929572c24b56f4c82e9f9bf709
	DOWNLOAD_URL="https://releases.hashicorp.com/terraform/${VER}/terraform_${VER}_linux_amd64.zip"
elif [ $# -eq 1 ] ; then
	VER=$1
    TERRAFORM_CHECKSUM=$2
	DOWNLOAD_URL="https://releases.hashicorp.com/terraform/${VER}/terraform_${VER}_linux_amd64.zip"
else
      echo "$USAGE"
      exit 1
fi

TERDIR="$PWD/terraform_test_artifacts"
if [ -x "$TERDIR/bin/terraform" ] ; then
    TERRAFORM_VERSION=`$TERDIR/bin/terraform --version -json | grep '"terraform_version":' | awk '{print $NF}' | sed 's/"//g' | sed 's/,$//'`
    if [ "$TERRAFORM_VERSION" == "$VER" ] ; then
        exit 0
    else 
        rm -rf ${TERDIR}/bin
    fi	
fi

pushd "$TERDIR"
`wget -q ${DOWNLOAD_URL} -O terraform_bin.zip`
## extract archive
unzip -o terraform_bin.zip 
terraform_bin=${TERDIR}/bin

mkdir -p "${terraform_bin}"
echo "${TERRAFORM_CHECKSUM}  terraform" | sha256sum -c \
    && chmod +x terraform \
    && mv terraform ${terraform_bin}
rm -rf terraform_bin.zip
popd
