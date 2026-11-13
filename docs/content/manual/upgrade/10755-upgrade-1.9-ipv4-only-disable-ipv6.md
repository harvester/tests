---
title: Upgrade from v1.9 keeps IPv4-only nodes IPv6-disabled (e2e_be)
---

* Related issues: [#10755](https://github.com/harvester/harvester/issues/10755) [#2688](https://github.com/harvester/tests/issues/2688)
* Related PR: harvester [#12143](https://github.com/harvester/harvester/pull/12143)

## Category:
* Upgrade Harvester

Dual-stack feature verification: [10880-dual-stack-ipv4-first-feature](../../deployment/10880-dual-stack-ipv4-first-feature). Fresh installs: [10755-dual-stack-ipv4-first-install](../../deployment/10755-dual-stack-ipv4-first-install).

## Background
v1.9 installers always wrote `/etc/sysctl.d/zz-harvester-enable-ipv6.conf` (`disable_ipv6 = 0`) in preparation for dual-stack, although the nodes were IPv4-only. From v1.10 the value follows `install.ipfamilies`. During an upgrade from `v1.9.x` the script `set_oem_ipv6_sysctl` writes `/oem/91_ipv6_sysctl.yaml` for nodes without IPv6 in `install.ipfamilies`, overriding the drop-in with `= 1`.

## Environment setup
1. Install **v1.9.x** (IPv4 only, 3 nodes; also a single-node cluster for the `command_single_node_upgrade` path).
1. On each node confirm the legacy state: `sysctl -n net.ipv6.conf.all.disable_ipv6` is `0` and `grep ipfamilies /oem/harvester.config` is empty.
1. On the 3-node cluster prepare the workload to check after the upgrade ("Workload survives the upgrade" below):
   * Cluster network config and VM networks: a VLAN network (for example VLAN 100 named `vlan100`) and the management network.
   * `storage-network` (VLAN 101, `192.168.101.0/24`) and `vm-migration-network` (VLAN 102, `192.168.102.0/24`) with IPv4 ranges.
   * Enable the addons that exist on v1.9: `vm-import-controller`, `pcidevices-controller`, `rancher-monitoring`, `rancher-logging`, `descheduler` and the experimental `kubeovn-operator`, and wait until they are Ready.
   * Two VMs (Ubuntu cloud image, qemu-guest-agent) on different nodes: `vm-vlan` with a NIC on `vlan100` and the management network, and `vm-overlay` on a kube-ovn overlay network. Write a marker file in each guest (`echo before-upgrade > /home/ubuntu/marker`).
   * Record the baseline: `kubectl get vmi -A -o wide`, `kubectl get nodes -o wide`, `kubectl get addons.harvesterhci.io -A`, `kubectl get settings.harvesterhci.io storage-network vm-migration-network`, `kubectl -n harvester-system get network-attachment-definitions`, and the service helper `kubectl get svc -A -o custom-columns="NAME:.metadata.name,POLICY:.spec.ipFamilyPolicy,FAMILIES:.spec.ipFamilies,IPS:.spec.clusterIPs" > before.txt`.

## Verification Steps
1. Upgrade to the v1.10 build under test. Watch the node upgrade logs (`/var/lib/rancher/... upgrade log` / `kubectl -n harvester-system logs -l harvesterhci.io/upgrade`) for `IPv6 is not enabled in harvester.config, keep the node IPv4-only`.
1. After each node reboots verify:
   * `sudo cat /oem/91_ipv6_sysctl.yaml` exists and contains `Written by harvester upgrade (IPv4-only install)`
   * `sudo sysctl -n net.ipv6.conf.{all,default,lo}.disable_ipv6` -> `1`
   * `cat /etc/sysctl.d/zz-harvester-enable-ipv6.conf` -> three keys `= 1`
   * `ip -6 -o addr show scope global` -> empty; the NetworkManager profile of device `mgmt-br` (`nmcli -t -f NAME,DEVICE connection show --active`, then `nmcli -g ipv6.method connection show <NAME>`) -> `disabled`
1. Reboot a node a second time: values remain `1` (persisted by the OEM file, not applied once).
1. Automated equivalent: `test_verify_ipv6_state` in `harvester_e2e_tests/integrations/test_upgrade.py` (it runs after the nodes are upgraded and is skipped when the upgrade target is older than v1.10).

### Workload survives the upgrade (3-node cluster)
1. After the upgrade finished and all nodes are Ready, compare with the baseline: `kubectl get vmi -A -o wide`, `kubectl get nodes -o wide`
1. Check `vm-vlan` and `vm-overlay`: the VMI is `Running`, the guest agent is connected, the VLAN IP and MAC are unchanged, and `cat /home/ubuntu/marker` still prints `before-upgrade`. Note whether the VM was restarted (`uptime` in the guest)
1. Reach `vm-vlan` on its VLAN IP from outside (ping and SSH) and from `vm-overlay`
1. Live migrate both VMs to another node and repeat steps 2 and 3
1. Check the networks: the cluster network config, `vlan100` and the NADs in `harvester-system` are unchanged; `kubectl get settings.harvesterhci.io storage-network vm-migration-network` shows the same values as before; `kubectl -n kube-system get ippools.whereabouts.cni.cncf.io` still lists the IPv4 pools; the Longhorn instance managers have their `lhnet1` address
1. Check the addons: `kubectl get addons.harvesterhci.io -A` shows the same addons enabled, the addon pods are Running and the chart versions moved to the v1.10 ones
1. The cluster stays single-stack. Run the service helper into `after.txt` and `diff before.txt after.txt`: every service is `SingleStack` `[IPv4]`; nodes have only an IPv4 `InternalIP`
1. Try to set `rangeV6` on `storage-network`; it is rejected with `rangeV6 is not supported: this cluster was not installed with dual-stack (IPv4+IPv6) networking`
1. Reboot the node that hosts `vm-vlan`; the VM comes back with the same IP

### Edge cases (on a throw-away node, before upgrading)
| setup | expected |
|---|---|
| previous version `v1.8.x` or already `v1.10.x` (re-run) | log `does not require updating the IPv6 sysctl settings`; no `/oem/91_ipv6_sysctl.yaml` created |
| `install.ipfamilies: [IPv4, IPv6]` in `/oem/harvester.config` | log `IPv6 is enabled ... keep the existing`; any stale `/oem/91_ipv6_sysctl.yaml` is removed; `disable_ipv6` stays `0` |
| `/oem/harvester.config` missing or not valid YAML | log `Cannot read install.ipfamilies`; no override created and an existing one is left untouched |
| `install.ipfamilies: [IPv4]` | override written (same as no key) |
| `UPGRADE_PREVIOUS_VERSION` unset | script calls `detect_upgrade` and still decides correctly |
| `v1.9.10` and later two-digit patch | the current regex `^v1\.9\.[0-9]$` does **not** match; confirm intended behaviour and raise an issue if not |

## Expected Results
* Every IPv4-only node upgraded from v1.9.x ends with kernel IPv6 disabled, persisted across reboots.
* Dual-stack or unreadable-config nodes are never flipped.
* Upgrade itself completes normally (all pods running, VMs/images/volumes intact, see [ipv6-dhcp-upgrade](../ipv6-dhcp-upgrade) for the generic post-upgrade checklist).
* Networks, `storage-network`, `vm-migration-network` and the enabled addons are intact after the upgrade.
* VMs on the VLAN and overlay networks are Running with unchanged addresses and data, can be live migrated, and survive a node reboot.
* The cluster is still single-stack; the dual-stack feature does not change any service or reject existing IPv4 configuration.
* Only the node IPv6 state is automated (`test_verify_ipv6_state`); the networks, VM and addon checks are manual.
