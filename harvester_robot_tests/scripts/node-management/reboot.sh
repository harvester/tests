#!/bin/bash
# Reboot node script
# Usage: reboot.sh &lt;hostname&gt; &lt;host_ip&gt;
HOSTNAME=$1
HOST_IP=$2
echo "Rebooting node: $HOSTNAME ($HOST_IP)"
# AWS example
if [ "$HOST_PROVIDER" == "aws" ]; then
INSTANCE_ID=$(cat /tmp/instance_mapping | jq -r ".\"$HOSTNAME\"")
aws ec2 reboot-instances --instance-ids $INSTANCE_ID
fi
# Vagrant example
if [ "$HOST_PROVIDER" == "vagrant" ]; then
cd $VAGRANT_CWD
vagrant reload $HOSTNAME
fi
echo "Node $HOSTNAME rebooted"