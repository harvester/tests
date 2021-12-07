#!/bin/bash

set -e

RANCHER_VERSION="v2.6.2"

if [ $# -eq 1 ] ; then
    RANCHER_VERSION=$1
fi

#Installing Kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" &> /dev/null
chmod +x kubectl
mv kubectl /usr/local/bin
#Start Docker 
systemctl enable docker &> /dev/null
systemctl start docker
#Install Rancher Server
docker run -d --restart=unless-stopped   -p 80:80 -p 443:443   --privileged   rancher/rancher:$RANCHER_VERSION &> /dev/null
sleep 90

for i in {1..6}; do
    #Get Bootstrap Password
    container_id=$(docker ps -a | grep "rancher/rancher:$RANCHER_VERSION" | awk '{print $1}')
    bootstrap_password=$(docker logs "${container_id}" 2>&1 | grep "Bootstrap Password:" | awk '{print $6}')
    if [ ! -z "$bootstrap_password" ] ; then
        echo $bootstrap_password
        break
    fi
    sleep 30
done

#Create .kube folder
KUBEDIR=/root/.kube
if [ ! -d $KUBEDIR ]; then
    mkdir $KUBEDIR
fi
