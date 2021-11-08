#!/bin/bash

set -e

#Installing Kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" &> /dev/null
chmod +x kubectl
mv kubectl /usr/local/bin
#Start Docker 
systemctl enable docker &> /dev/null
systemctl start docker
#Install Rancher Server
docker run -d --restart=unless-stopped   -p 80:80 -p 443:443   --privileged   rancher/rancher:v2.6.2 &> /dev/null
sleep 200 
#Get Bootstrap Password
container_id=$(docker ps -a | grep "rancher/rancher:v2.6.2" | awk '{print $1}')
echo $(docker logs "${container_id}" 2>&1 | grep "Bootstrap Password:" | awk '{print $6}')

#Create .kube folder
KUBEDIR=/root/.kube
if [ ! -d $KUBEDIR ]; then
    mkdir $KUBEDIR
fi
