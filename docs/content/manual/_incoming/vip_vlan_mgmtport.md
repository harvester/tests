---
title: VIP is accessibility with VLAN enabled on management port
---
Ref: https://github.com/harvester/harvester/issues/1722

## Verify Items
  - VIP should be accessible when VLAN enabled on management port

## Case: Single Node enables VLAN on management port
1. Install Harvester with single node
1. Login to dashboard then navigate to Settings
1. Edit **vlan** to enable VLAN on `harvester-mgmt`
1. reboot the node
1. after reboot, login to console
1. Run the command should not contain any output
    - `sudo -s`
    - `kubectl get pods -A --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep harvester-network-controller-manager | xargs kubectl logs -n harvester-system | grep "Failed to update lock"`
1. Repeat step 4-6 with 10 times, should not have any error
