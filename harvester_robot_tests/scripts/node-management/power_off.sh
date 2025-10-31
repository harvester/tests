#!/bin/bash
# Power off node script
# Usage: power_off.sh &lt;hostname&gt; &lt;host_ip&gt;
HOSTNAME=$1
HOST_IP=$2
echo "Powering off node: $HOSTNAME ($HOST_IP)"
# AWS example
if [ "$HOST_PROVIDER" == "aws" ]; then
INSTANCE_ID=$(cat /tmp/instance_mapping | jq -r ".\"$HOSTNAME\"")
aws ec2 stop-instances --instance-ids $INSTANCE_ID
fi
# Vagrant example
if [ "$HOST_PROVIDER" == "vagrant" ]; then
cd $VAGRANT_CWD
vagrant halt $HOSTNAME
fi
echo "Node $HOSTNAME powered off"