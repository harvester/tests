---
title: Install Harvester with dual-stack (IPv4 first) networking
---

* Related issues: [#10755](https://github.com/harvester/harvester/issues/10755) [#10795](https://github.com/harvester/harvester/issues/10795) [#10796](https://github.com/harvester/harvester/issues/10796) [#2688](https://github.com/harvester/tests/issues/2688)
* Related PRs: harvester-installer [#1298](https://github.com/harvester/harvester-installer/pull/1298), harvester [#11309](https://github.com/harvester/harvester/pull/11309)

## Category:
* Deployment / Network

## Environment setup
1. Libvirt network (or lab VLAN) offering **IPv4 DHCP and IPv6 SLAAC or DHCPv6**, e.g. the `workload` network in [ipv6-dhcp-upgrade](../../upgrade/ipv6-dhcp-upgrade).
1. A second network/VLAN with **IPv4 only** (no router advertisements) for the negative case.
1. Source of truth on a node: `install.ipfamilies` in `/oem/harvester.config` (`["IPv4"]` or `["IPv4","IPv6"]`).

## Verification Steps

### A. Installer UI (ISO, `create` mode)
1. On *Configure network* confirm the new dropdown **Network type** with `IPv4 only` (default) and `IPv4,IPv6 (dual-stack, IPv4-first)`. Check it appears with both DHCP and Static IPv4 method.
1. Select dual-stack, press Enter: a red experimental WARNING appears and focus stays on the dropdown. Press Enter again to continue; in a second run press ESC instead and confirm nothing was applied.
1. Select dual-stack on the **IPv4-only network**: after confirm the installer must fail with `no non-link-local IPv6 address found on interface mgmt-br ...` (waits ~15s) and not proceed.
1. Go back, switch to `IPv4 only`, change again to dual-stack: warning is shown again (acknowledgement is reset).
1. On *Cluster network* page verify prefilled defaults
   * IPv4 only: pod `10.52.0.0/16`, service `10.53.0.0/16`, DNS `10.53.0.10`
   * dual-stack: pod `10.52.0.0/16,fd52::/56`, service `10.53.0.0/16,fd53::/112`, DNS `10.53.0.10,fd53::a`
1. Go back to *Configure network*, flip the type, return: defaults follow the newly selected type.
1. Negative input on the Cluster network page (each must show a red message and block Next):

   | field | value | mode | reason |
   |---|---|---|---|
   | pod | `fd52::/56` | any | single CIDR must be IPv4 |
   | pod | `fd52::/56,10.52.0.0/16` | dual | IPv6-first order |
   | pod | `10.52.0.0/16,fd52::/56` | IPv4 only | mode needs single IPv4 CIDR |
   | pod | `10.52.0.0/16` | dual | dual-stack needs both |
   | pod | `10.52.0.0/16,fd52::/56,10.54.0.0/16` | dual | max two |
   | service | `10.52.0.0/24` with pod `10.52.0.0/16` | any | overlap |
   | service | single with dual pod CIDR (or reverse) | dual | count mismatch |
   | DNS | `10.54.0.10` | any | outside service CIDR |
   | DNS | `10.53.0.0` | any | network address |
   | DNS | `fd53::a` | any | single DNS must be IPv4 |
   | DNS | `fd53::a,10.53.0.10` | dual | IPv4-first order |
   | DNS | `10.53.0.10,fd53::a` | IPv4 only | needs single IPv4 DNS |

### B. Node state after install (run on every node, repeat for `join` mode and PXE with `install.ipfamilies` in config.yaml)
Dual-stack expectations vs IPv4-only expectations:

| check (command) | dual-stack | IPv4 only |
|---|---|---|
| `sudo sysctl -n net.ipv6.conf.{all,default,lo}.disable_ipv6` | `0` | `1` |
| `cat /etc/sysctl.d/zz-harvester-enable-ipv6.conf` | three keys `= 0`, header `dual-stack install` | three keys `= 1`, header `IPv4-only install` |
| `ip -6 -o addr show dev mgmt-br scope global` | at least one SLAAC/DHCPv6 address | empty |
| `nmcli -t -f NAME,DEVICE connection show --active` to find the profile of device `mgmt-br`, then `nmcli -g ipv6.method connection show <NAME>` (same for the VLAN device when a VLAN is used) | `auto` (`addr-gen-mode=stable-privacy`, `ip6-privacy=0`) | `disabled` |
| `kubectl get node -o jsonpath='{.items[*].spec.podCIDRs}'` | one IPv4 + one IPv6 range per node | IPv4 only |
| `kubectl get svc kubernetes -o jsonpath='{.spec.ipFamilies}'` | `["IPv4","IPv6"]` | `["IPv4"]` |
| `kubectl -n kube-system get svc rke2-coredns-rke2-coredns -o jsonpath='{.spec.clusterIPs}'` | IPv4 + IPv6 DNS | IPv4 only |

1. Reboot a node: all of the above still hold (sysctl is persisted, not just applied at runtime).
1. Dual-stack: `ping -6` between two nodes' global addresses; create a pod/VM and check it receives both pod IPs (`kubectl get pod -o jsonpath='{.status.podIPs}'`).
1. IPv4-only: `ping -6 ::1` fails; `ip -6 addr` shows no `lo` `::1`.
1. Automated equivalent: `pytest harvester_e2e_tests/integrations/test_ipv6_host.py` (it reads `ipfamilies` and asserts the table above via API + SSH).

### C. Unattended / PXE / re-run
1. Config file (PXE/`install.automatic`) with `install.ipfamilies: [IPv4, IPv6]`: same results as B, no UI warning.
1. Config without `ipfamilies`: behaves as IPv4-only (`disable_ipv6 = 1`).
1. Install failure at the IPv6 check, then pressing Enter again re-triggers address assignment (stable-privacy self-healing) and succeeds once the network offers IPv6.

## Expected Results
* All UI validations behave as listed; invalid combinations never reach installation.
* Kernel, drop-in, NetworkManager, Kubernetes node/service data are consistent with the selected IP family on every node, before and after reboot.
* Mixed clusters (some nodes dual-stack, some IPv4-only) are not a supported outcome; `join` mode dialog must offer IPv6 choice consistently with the cluster.
