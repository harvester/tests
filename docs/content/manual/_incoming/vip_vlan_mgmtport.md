---
title: VIP is accessibility with VLAN enabled on management port
---
Ref: https://github.com/harvester/harvester/issues/1722

## Verify Items
  - VIP should be accessible when VLAN enabled on management port

## Case: Single Node enables VLAN on management port
1. Install Harvester with single node
2. Login to dashboard then navigate to Settings
3. Edit **vlan** to enable VLAN on `harvester-mgmt`
4. reboot the node
5. after reboot, login to console
6. Run the command should not contain any output
    - `sudo -s`
    - `kubectl get pods -A --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}' | grep harvester-network-controller-manager | xargs kubectl logs -n harvester-system | grep "Failed to update lock"`
7. Repeat step 4-6 with 10 times, should not have any error
