#!/bin/bash
# Power on node script
# Usage: power_on.sh &lt;hostname&gt; &lt;host_ip&gt;
HOSTNAME=$1
HOST_IP=$2
echo "Powering on node: $HOSTNAME ($HOST_IP)"
# AWS example
if [ "$HOST_PROVIDER" == "aws" ]; then
INSTANCE_ID=$(cat /tmp/instance_mapping | jq -r ".\"$HOSTNAME\"")
aws ec2 start-instances --instance-ids $INSTANCE_ID
fi
# Vagrant example
if [ "$HOST_PROVIDER" == "vagrant" ]; then
cd $VAGRANT_CWD
vagrant up $HOSTNAME
fi
echo "Node $HOSTNAME powered on"