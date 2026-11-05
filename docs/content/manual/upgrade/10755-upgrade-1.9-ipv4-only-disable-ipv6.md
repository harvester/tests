---
title: Upgrade from v1.9 keeps IPv4-only nodes IPv6-disabled
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

## Verification Steps
1. Upgrade to the v1.10 build under test. Watch the node upgrade logs (`/var/lib/rancher/... upgrade log` / `kubectl -n harvester-system logs -l harvesterhci.io/upgrade`) for `IPv6 is not enabled in harvester.config, keep the node IPv4-only`.
1. After each node reboots verify:
   * `sudo cat /oem/91_ipv6_sysctl.yaml` exists and contains `Written by harvester upgrade (IPv4-only install)`
   * `sudo sysctl -n net.ipv6.conf.{all,default,lo}.disable_ipv6` -> `1`
   * `cat /etc/sysctl.d/zz-harvester-enable-ipv6.conf` -> three keys `= 1`
   * `ip -6 -o addr show scope global` -> empty; the NetworkManager profile of device `mgmt-br` (`nmcli -t -f NAME,DEVICE connection show --active`, then `nmcli -g ipv6.method connection show <NAME>`) -> `disabled`
1. Reboot a node a second time: values remain `1` (persisted by the OEM file, not applied once).
1. `pytest harvester_e2e_tests/integrations/test_ipv6_host.py` passes against the upgraded cluster.

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
