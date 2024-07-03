#!/bin/bash

set -e

USAGE="${0}: [<version>] 
Where:
  <version>: version of to dowload. If absent, it will download the latest.
"

DOWNLOAD_URL=
if [ $# -eq 0 ] ; then
	# lookup the latest release download URL
	VER=$(curl -s https://releases.hashicorp.com/terraform/ | grep -Po "href=\"/terraform/\K(.[^-]+?)(?=/)" | head -1)
	DOWNLOAD_URL="https://releases.hashicorp.com/terraform/${VER}/terraform_${VER}_linux_amd64.zip"
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
`wget -q ${DOWNLOAD_URL} -O terraform_bin.zip`
## extract archive
unzip -o terraform_bin.zip 
terraform_bin=${TERDIR}/bin

mkdir -p "${terraform_bin}"
mv terraform ${terraform_bin}
rm -rf terraform_bin.zip
popd
