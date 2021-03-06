#!/bin/bash

set -e

USAGE="${0}: [<version>] 
Where:
  <version>: version of to dowload. If absent, it will download the latest.
"

DOWNLOAD_URL=
if [ $# -eq 0 ] ; then
	# lookup the latest release download URL
	DOWNLOAD_URL="https://releases.hashicorp.com/terraform/1.0.9/terraform_1.0.9_linux_amd64.zip"
	VER=$(curl -s https://api.github.com/repos/hashicorp/terraform/releases/latest | grep '"name":' | awk '{print $2}' | sed 's/.*v//' | sed 's/".*//')
elif [ $# -eq 1 ] ; then
	VER=$1
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
`wget ${DOWNLOAD_URL} -O terraform_bin.zip`
## extract archive
unzip terraform_bin.zip 
terraform_bin=${TERDIR}/bin

mkdir -p "${terraform_bin}"
mv terraform ${terraform_bin}
rm -rf terraform_bin.zip
popd
