---
title: Dual-stack (IPv4 first) feature verification
---

* Related issues: [#10755](https://github.com/harvester/harvester/issues/10755) [#10769](https://github.com/harvester/harvester/issues/10769) [#10880](https://github.com/harvester/harvester/issues/10880) [#11471](https://github.com/harvester/harvester/issues/11471) [#2688](https://github.com/harvester/tests/issues/2688)
* Related PRs: harvester [#10945](https://github.com/harvester/harvester/pull/10945) [#11309](https://github.com/harvester/harvester/pull/11309) [#11523](https://github.com/harvester/harvester/pull/11523) [#11877](https://github.com/harvester/harvester/pull/11877) [#12095](https://github.com/harvester/harvester/pull/12095), harvester-installer [#1298](https://github.com/harvester/harvester-installer/pull/1298), charts [#636](https://github.com/harvester/charts/pull/636) [#643](https://github.com/harvester/charts/pull/643) [#645](https://github.com/harvester/charts/pull/645), node-manager [#238](https://github.com/harvester/node-manager/pull/238), kubeovn-operator [#52](https://github.com/harvester/kubeovn-operator/pull/52)
* HEP: [20260528-dual-stack-ipv4-first](https://github.com/harvester/harvester/blob/master/enhancements/20260528-dual-stack-ipv4-first.md)

## Category:
* Deployment / Network / Virtual Machine

The installer UI, config-file install and the upgrade path are in [10755-dual-stack-ipv4-first-install](../10755-dual-stack-ipv4-first-install) and [10755-upgrade-1.9-ipv4-only-disable-ipv6](../../upgrade/10755-upgrade-1.9-ipv4-only-disable-ipv6). This case verifies the running cluster. The kernel, sysctl and NetworkManager checks (install plan, "Node state after install") are not repeated here and apply to both clusters.

## Environment setup
1. **Cluster A (IPv4 only):** 2 nodes, installed from the build under test with the default network type.
1. **Cluster B (dual-stack):** 2 nodes, `node-1` created and `node-2` joined with network type `IPv4,IPv6 (dual-stack, IPv4-first)`. Values: pod `10.52.0.0/16,fd52::/56`, service `10.53.0.0/16,fd53::/112`, DNS `10.53.0.10,fd53::a`.
1. libvirt network for cluster B with IPv4 and IPv6 DHCP, NAT with `ipv6="yes"`, for example `192.168.103.0/24` and `fd00:cafe:4::/64` (`virbr4`).
1. Ubuntu cloud image (netplan based) uploaded to Images on both clusters.
1. Service helper used below:
   ```
   kubectl get svc -A -o custom-columns="NAME:.metadata.name,POLICY:.spec.ipFamilyPolicy,FAMILIES:.spec.ipFamilies,IPS:.spec.clusterIPs"
   ```

## Verification Steps

### Cluster A: IPv4-only regression
1. Run the "IPv4 only" column of "Node state after install" in the install plan on every node, before and after a reboot
1. Run the service helper with all addons disabled
1. Enable `harvester-seeder`, `pcidevices-controller`, `vm-import-controller` and `kubeovn-operator`
1. Run `sudo grep -E 'ipFamilyPolicy|netStack|dualStack' /etc/rancher/rancherd/config.yaml.d/22-addons.yaml` and the service helper again
1. Configure `storage-network`, `vm-migration-network` and `rwx-network` with IPv4 ranges only (VLAN 100, 101, 102 on `mgmt`, `192.168.100.0/24`, `192.168.101.0/24`, `192.168.102.0/24`) and run `kubectl -n kube-system get ippools.whereabouts.cni.cncf.io`
1. Create a VM on the management network, run `kubectl get vmi <vm> -o jsonpath='{.status.interfaces[0].ipAddresses}'` and `ip -6 addr` in the guest
1. Disable `kubeovn-operator` while no VM uses an overlay network
1. Read the VIP with `kubectl -n harvester-system get configmap vip -o jsonpath='{.data.ip}'` and request a kubeconfig as in "VIP and kubeconfig" below

### Cluster B: host, node join and pods
1. Run the "dual-stack" column of "Node state after install" in the install plan on every node, before and after a reboot
1. Run `ip -6 route show default` and `cat /etc/rancher/rke2/config.yaml.d/90-harvester-server.yaml`
1. Run `kubectl get node -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.podCIDRs}{"\n"}{end}'` and `kubectl get svc kubernetes -o jsonpath='{.spec.clusterIPs}{"\n"}{.spec.ipFamilies}'`
1. Check the joined node: `kubectl get node node-2 -o jsonpath='{.status.addresses}'`, `kubectl get machines -n fleet-local`, `kubectl get nodes -o wide`
1. Create `pod-a` and `pod-b` (`kubectl run pod-a --image=busybox --restart=Never -- sleep 3600`), once on the same node and once on different nodes, and run `kubectl get pod pod-a -o jsonpath='{.status.podIPs}'`
1. Run `kubectl exec pod-a -- ping -6 -c3 <pod-b IPv6>` and `kubectl exec pod-a -- ping -c3 <pod-b IPv4>`
1. Run `kubectl exec pod-a -- nslookup kubernetes.default.svc.cluster.local 10.53.0.10` and the same with `fd53::a`. Use the FQDN: the original run used the short name and got NXDOMAIN on both servers, so DNS over IPv6 was not proven there
1. Open `https://[fd00:cafe:4::xxx]/`, run `ssh rancher@fd00:cafe:4::xxx` and `ping -6` between the nodes
1. Delete the test pods

### Cluster B: services and addons
1. Run the service helper with all addons disabled
1. Run `kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}: {.status.addresses}{"\n"}{end}'`
1. Check that `kubectl exec -n harvester-system <harvester-node-manager pod> -- sha256sum /usr/bin/harvester-node-manager` matches a local build of the same commit (disable the docker cache when building)
1. Run `sudo grep ipFamilyPolicy /etc/rancher/rancherd/config.yaml.d/22-addons.yaml` and check the `kubeovn-operator` values in the same file
1. Enable `harvester-seeder`, `pcidevices-controller`, `vm-import-controller` and `kubeovn-operator`, wait until Ready, and run `kubectl get svc -A -o custom-columns="NAME:.metadata.name,POLICY:.spec.ipFamilyPolicy,FAMILIES:.spec.ipFamilies" | grep -E 'ovn|pci|import|seeder'`
1. Enable more advertised addons: `rancher-monitoring`, `rancher-logging`, `descheduler` and `nvidia-driver-toolkit` (needs a vGPU driver location, skip without one), together with the four addons above, wait until Ready and run `kubectl get addons.harvesterhci.io -A` and `kubectl get pods -A | grep -vE 'Running|Completed'`
1. For each enabled addon record the service families in its namespace: `kubectl get svc -n cattle-monitoring-system -o custom-columns="NAME:.metadata.name,POLICY:.spec.ipFamilyPolicy,FAMILIES:.spec.ipFamilies"` (same for `cattle-logging-system`, `kube-system`, `harvester-system`)
1. Exercise each addon on the dual-stack cluster:
   * `rancher-monitoring`: open Grafana and Prometheus from the dashboard, the node and VM dashboards show data and the Prometheus targets are `UP`
   * `rancher-logging`: pods Running; create a `ClusterOutput`/`ClusterFlow` (or use the default flows) and see logs arrive; check the fluentbit/fluentd pods have IPv4 and IPv6 pod IPs
   * `descheduler`: the deployment is Running and the logs show a descheduling cycle without errors
   * `pcidevices-controller`: `kubectl get pcidevices` lists devices on hardware that has them (the list can be empty in nested virtualization)
   * `harvester-seeder`: pods Running (hardware features need bare metal)
   * `vm-import-controller`: the CRDs exist (`kubectl get crd | grep migration.harvesterhci.io`); optionally import a VM from a VMware or OpenStack source as in the vm-import plan
   * `kubeovn-operator`: create an overlay network and a VM on it (see VM section)
1. Optional chart check in the charts repository: `helm template` each chart (harvester-load-balancer, harvester-network-controller, harvester-node-disk-manager, harvester-seeder, harvester-pcidevices-controller, harvester-vm-import-controller, kubeovn-operator) with and without `--set global.ipFamilyPolicy=PreferDualStack`, and in the harvester repository `go run ./cmd/addon-generator -generateTemplates -path ./test/.`

### Cluster B: VIP and kubeconfig
1. Read the VIP: `VIP=$(kubectl -n harvester-system get configmap vip -o jsonpath='{.data.ip}')`
1. Get a token: `TOKEN=$(kubectl -n cattle-system get secret <harvester-api-service-token-xxxxx> -o jsonpath='{.data.token}' | base64 -d)`
1. Request a kubeconfig:
   ```
   curl -sk -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"clusterRoleName":"cluster-admin","namespace":"default","serviceAccountName":"test-kubeconfig-sa"}' \
     "https://${VIP}/v1/harvester/kubeconfig" | grep -o 'server: [^\\]*'
   ```
1. Repeat step 3 against `https://[fd00:cafe:4::xxx]/v1/harvester/kubeconfig` and use the file with `kubectl --kubeconfig <file> get nodes`. The PR only recorded the IPv4 result, this IPv6 step is new coverage
1. Apply these `vip-pools` values (setting is deprecated) with `kubectl patch settings.harvesterhci.io vip-pools --type merge -p '{"value":"{\"default\":\"<value>\"}"}'`: `192.168.100.0/24`, `192.168.100.10-192.168.100.20`, `2001:db8::/120`, `2001:db8::1-2001:db8::ff`, `192.168.100.0/24,2001:db8::/120`, `192.168.100.10-192.168.100.20,2001:db8::1-2001:db8::ff`
1. Apply `{"testpool":"10.0.0.50-10.0.0.60"}` as the whole value, wait 3 seconds and run `kubectl -n kube-system get configmap kubevip -o jsonpath='{.data}'`
1. Enable `kubeovn-operator`, create an overlay network, attach a VM (with an IPv6 address) to it and run `kubectl patch addon kubeovn-operator -n kube-system --type merge -p '{"spec":{"enabled":false}}'`

### Cluster B: storage, RWX and migration networks
1. Set `storage-network` to `{"vlan":100,"clusterNetwork":"mgmt","range":"192.168.100.0/24","rangeV6":"fd00::/120","rangeV6Start":"fd00::10","rangeV6End":"fd00::50"}`
1. Run `kubectl -n harvester-system get network-attachment-definitions | grep storagenetwork`, then `kubectl -n harvester-system get network-attachment-definitions <name> -o jsonpath='{.spec.config}'` and `kubectl -n kube-system get ippools.whereabouts.cni.cncf.io`
1. For each Longhorn instance manager run `kubectl -n longhorn-system get pod <instance-manager> -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}'` and `kubectl -n kube-system get ippools.whereabouts.cni.cncf.io fd00---120 -o jsonpath='{.spec.allocations}'`
1. Set `rwx-network` to `{"share-storage-network":false,"network":{"vlan":102,"clusterNetwork":"mgmt","range":"192.168.102.0/24","rangeV6":"fd02::/120","rangeV6Start":"fd02::10","rangeV6End":"fd02::50"}}`, check the NAD and pools as above, then create an RWX volume and attach it to a VM
1. Set `vm-migration-network` to `{"vlan":101,"clusterNetwork":"mgmt","range":"192.168.101.0/24","rangeV6":"fd01::/120","rangeV6Start":"fd01::10","rangeV6End":"fd01::50"}`
1. Migrate the VM from the VM section to the other node. During the migration run `kubectl -n kube-system get ippools.whereabouts.cni.cncf.io fd01---120 -o yaml`
1. After the migration run `kubectl get vmi <vm> -o jsonpath='{.status.interfaces[*]}'`

### Cluster B: NTP servers
1. Baseline: `kubectl get settings.harvesterhci.io ntp-servers -o jsonpath='{.value}'` is `{"ntpServers":["0.suse.pool.ntp.org"]}`
1. Set a mixed list: `kubectl patch settings.harvesterhci.io ntp-servers --type merge -p '{"value":"{\"ntpServers\":[\"fd00::1\",\"0.suse.pool.ntp.org\",\"192.0.2.1\",\"2001:db8::123\"]}"}'`
1. Run `kubectl get nodeconfig <node> -n harvester-system -o jsonpath='{.metadata.generation} {.spec.ntpConfigs.ntpServers} {.metadata.annotations.AppliedConfig}{"\n"}'`
1. On the node run `cat /etc/systemd/timesyncd.conf` and `timedatectl show-timesync`
1. Run `kubectl logs -n harvester-system <harvester-node-manager pod> | grep -i ntp`
1. Patch the same servers in another order (`192.0.2.1`, `fd00::1`, `2001:db8::123`, `0.suse.pool.ntp.org`) and check again
1. Patch the setting back to `["0.suse.pool.ntp.org"]`, reboot a node and check `timesyncd.conf`

### Cluster B: VM with IPv6 through cloud-init
On a dual-stack cluster KubeVirt configures only IPv4 in the guest (DHCPv4). The IPv6 address and default route must come from cloud-init, see the [KubeVirt docs](https://kubevirt.io/user-guide/network/interfaces_and_networks/#masquerade-ipv4-and-ipv6-dual-stack-support), [#11748](https://github.com/harvester/harvester/issues/11748) and [kubevirt#19193](https://github.com/kubevirt/kubevirt/issues/19193). For masquerade the guest values are fixed: address `fd10:0:2::2/120`, gateway `fd10:0:2::1`.
1. Create a VM on the management network without any IPv6 configuration, run `kubectl get pod -l vm.kubevirt.io/name=<vm> -o jsonpath='{.items[0].status.podIPs}'` and `ip -4 addr`, `ip -6 addr`, `ip -6 route` in the guest
1. Create a VM with this user data (Advanced Options -> Cloud Config). Check the interface name with `ip link` and adjust `enp1s0` if needed:
   ```
   #cloud-config
   package_update: true
   packages:
     - qemu-guest-agent

   user: ubuntu
   password: password1234
   chpasswd: { expire: False }
   ssh_pwauth: true

   write_files:
     - path: /etc/netplan/99-dualstack.yaml
       permissions: '0600'
       content: |
         network:
           version: 2
           ethernets:
             enp1s0:
               dhcp4: true
               addresses:
                 - fd10:0:2::2/120
               routes:
                 - to: default
                   via: fd10:0:2::1
                   metric: 50
                   on-link: true

   runcmd:
     - netplan apply
     - systemctl enable --now qemu-guest-agent.service
   ```
1. Do not change the network manually inside the VM. Run `kubectl get vmi <vm> -o jsonpath='{.status.interfaces[0].ipAddresses}'`, then `ip -6 addr` and `ip -6 route` in the guest
1. From a node run `ping -6` and `ssh ubuntu@<pod IPv6 of the VM>`, from another pod or VM run `ping -6`, from the guest run `ping -6 -c3 <IPv6 address of a node>`
1. Optional: run `python3 -m http.server 8080` in the guest and `curl -g "http://[<pod IPv6>]:8080"` from a node
1. Stop and start the VM and check the addresses and route again
1. Repeat step 2 to 4 on a VLAN network and on a kube-ovn overlay network and note whether the guest needs manual configuration (the issue says all supported networks are affected)

### Negative scenarios
Previous setting values must stay in place after each rejected request.

| # | Cluster | Input | Expected message |
|---|---|---|---|
| 1 | A | `storage-network`, `vm-migration-network` or `rwx-network` with `rangeV6`, `rangeV6Start`, `rangeV6End` (also with only `rangeV6`) | `rangeV6 is not supported: this cluster was not installed with dual-stack (IPv4+IPv6) networking` |
| 2 | B | `storage-network` with only `rangeV6` `fd00::/120` | `rangeV6Start and rangeV6End are required alongside rangeV6: name one contiguous allocatable window` |
| 3 | B | `rangeV6Start` `fd99::10`, `rangeV6End` `fd00::50` | `rangeV6Start fd99::10 is not within rangeV6 fd00::/120` |
| 4 | B | `rangeV6Start` `fd00::10`, `rangeV6End` `fd99::50` | `rangeV6End fd99::50 is not within rangeV6 fd00::/120` |
| 5 | B | `rangeV6Start` `fd00::50`, `rangeV6End` `fd00::10` | `rangeV6Start fd00::50 must not be after rangeV6End fd00::10` |
| 6 | B | `vm-migration-network` with `rangeV6` `fd00::/120` (`fd00::40` to `fd00::60`) while `storage-network` uses `fd00::/120` | `vm-migration-network: ... the network configuration is overlapped with storage-network` |
| 7 | B | `vip-pools` `2001:db8::1-2001:db8::ff,192.168.100.10-192.168.100.20` | `IPv4 entries must precede IPv6 entries` |
| 8 | B | `vip-pools` `172.16.4.10-2001:db8::1` | `cannot mix IPv4 and IPv6 addresses` |
| 9 | B | `vip-pools` `not-an-ip` | `invalid IP Range value not-an-ip of default` |
| 10 | A and B | `ntp-servers` with `["0.suse.pool.ntp.org","0.suse.pool.ntp.org","1.suse.pool.ntp.org"]` | `value: duplicate NTP server: [0.suse.pool.ntp.org]` |

## Expected Results

### Cluster A: IPv4-only regression
1. The node state matches the "IPv4 only" column of the install plan, before and after the reboot
1. Every service is `SingleStack` `[IPv4]` with one cluster IP and the nodes have only an IPv4 `InternalIP`, before and after enabling the addons
1. `22-addons.yaml` has `ipFamilyPolicy: SingleStack`, `netStack: ipv4` and no `dualStack:` block; all addon services (including `kube-ovn-*`, `ovn-*`, `pcidevices-webhook`) are `SingleStack` `[IPv4]`
1. The IPv4 networks are accepted, pools such as `192.168.100.0-24` exist and Longhorn instance managers get an IPv4 `lhnet1` address
1. The VMI has one IPv4 address and the guest has no global IPv6 address
1. `kubeovn-operator` can be disabled when no VM uses an overlay network
1. The VIP is a plain IPv4 address and the kubeconfig has `server: https://<VIP>:6443/`

### Cluster B: host, node join and pods
1. The node state matches the "dual-stack" column of the install plan, before and after the reboot
1. The default IPv6 route is `proto ra`
1. `cluster-cidr`, `service-cidr` and `cluster-dns` hold the dual-stack values
1. Each node has one IPv4 and one IPv6 pod CIDR (for example `["10.52.0.0/24","fd52::/64"]`); the `kubernetes` service stays `["10.53.0.1"]` `["IPv4"]`, which is expected (non goal of the Kubernetes dual-stack KEP)
1. `node-2` has an IPv4 and an IPv6 `InternalIP`, both machines are `READY True` and both nodes are `Ready`
1. Each pod has an address from `10.52.x.x` and from `fd52::`; IPv4 and IPv6 ping have 0% loss on the same node and across nodes
1. Both cluster DNS addresses answer the FQDN lookup (file a bug if the IPv6 one does not)
1. The dashboard loads and login works over IPv6, SSH works, nodes ping each other over IPv6

### Cluster B: services and addons
1. Each node has an IPv4 and an IPv6 `InternalIP`
1. These services are `PreferDualStack` `[IPv4 IPv6]` with two cluster IPs: `harvester`, `harvester-webhook`, `harvester-load-balancer-webhook`, `harvester-network-webhook`, `harvester-node-disk-manager-webhook`, `harvester-node-manager-webhook`, `cdi-api`, `cdi-uploadproxy`, `cdi-prometheus-metrics`, `kubevirt-operator-webhook`, `virt-api`, `virt-exportproxy`, `harvester-cluster-repo`, `rke2-coredns-rke2-coredns` (`10.53.0.10`, `fd53::a`), `rke2-metrics-server`, `rke2-traefik`; `kubevirt-prometheus-metrics` is headless (`[None]`)
1. These stay `SingleStack` `[IPv4]` because of upstream gaps and are not a bug: `kubernetes`, `rancher*`, `capi-webhook-service`, `imperative-api-extension`, `gitjob`, `monitoring-fleet-controller`, `monitoring-gitjob`, `longhorn-*` ([#11628](https://github.com/harvester/harvester/issues/11628) [#11614](https://github.com/harvester/harvester/issues/11614) [#12030](https://github.com/harvester/harvester/issues/12030))
1. The node-manager binary hash matches the local build
1. `22-addons.yaml` has four lines `ipFamilyPolicy: PreferDualStack`, `netStack: dual_stack` and a `dualStack:` block (`podCIDR: 10.54.0.0/16,fd54::/112`, `serviceCIDR: 10.55.0.0/16,fd55::/112`, `joinCIDR: 100.64.0.0/16,fd64::/112`, `podGateway: 10.54.0.1,fd54::1`) that does not overlap the RKE2 CIDRs
1. `harvester-seeder`, `harvester-vm-import-controller`, `pcidevices-webhook`, `kube-ovn-cni`, `kube-ovn-controller`, `kube-ovn-monitor`, `kube-ovn-pinger`, `kubeovn-operator-*`, `ovn-nb`, `ovn-northd`, `ovn-sb` are `PreferDualStack` `[IPv4 IPv6]`. This also verifies the `netStack` fix in kubeovn-operator #52, the operator-created `kube-ovn-*` services could not switch before
1. All addons enabled above are Ready and no pod is stuck outside `Running` or `Completed`
1. Addon services owned by Harvester are `PreferDualStack`; Rancher-owned charts (`rancher-monitoring`, `rancher-logging`) are expected to stay `SingleStack` until Rancher adopts dual-stack ([#11614](https://github.com/harvester/harvester/issues/11614)); record the result for `descheduler` and `nvidia-driver-toolkit`; any other single-stack service Harvester owns is a finding to report
1. Grafana and Prometheus load with data and all Prometheus targets are `UP`; logs arrive through the logging addon; the descheduler runs without errors; `pcidevices` and `vm-import-controller` objects work as far as the environment allows
1. `kube-ovn-webhook` stays `SingleStack` on purpose ([#10882](https://github.com/harvester/harvester/issues/10882)). Not dual-stack yet and out of scope: `harvester-vm-dhcp-controller`, `harvester-upgrade-manager`, `harvester-csi-driver-lvm`, `harvester-mcp-server`, `rancher-vcluster` ([#10768](https://github.com/harvester/harvester/issues/10768) [#12043](https://github.com/harvester/harvester/issues/12043))
1. Charts render `SingleStack` by default and `PreferDualStack` with the value set; `networking.netStack` defaults to `ipv4`; the generated addon template keeps the `{{- if .IsDualStackEnabled }}` blocks, which are resolved on the node at install time

### Cluster B: VIP and kubeconfig
1. The IPv4 form is unchanged; the IPv6 server is `https://[<ipv6>]:6443/` with brackets and the kubeconfig works
1. All six `vip-pools` values are accepted and the kubevip configmap contains `{"range-testpool":"10.0.0.50-10.0.0.60"}`
1. Disabling `kubeovn-operator` is rejected with `kubeovn-operator addon cannot be disabled as VMs attached to overlay network ... are still in use`, also when the VM only has an IPv6 address

### Cluster B: storage, RWX and migration networks
1. The `storagenetwork-*` NAD uses `whereabouts` with two `ipRanges` (the IPv4 range and the IPv6 range with `range_start` and `range_end`) and pool `fd00---120` exists
1. Each instance manager has IPv4 and IPv6 on `eth0` and on `lhnet1` (for example `192.168.100.1` and `fd00::10`), allocations are listed with `ifname: lhnet1`
1. The RWX NAD has both ranges, pool `fd02---120` exists and the RWX volume is healthy
1. `virt-handler` pods hold `migration0` addresses, the migration succeeds, and the `virt-launcher` pod holds an address from the migration pool while migrating
1. Known gap, record it and do not fail: after the migration the VMI status keeps only the primary IP

### Cluster B: NTP servers
1. The mixed list is accepted, the node config generation increases and `AppliedConfig` equals the list
1. `timesyncd.conf` has `NTP = fd00::1 0.suse.pool.ntp.org 192.0.2.1 2001:db8::123` and `SystemNTPServers` shows the four entries
1. The log shows `Prepare to update NTP server with: ...` once, then `NTP config is not changed` (no endless reconcile)
1. The order is kept, not sorted, and a new order triggers one reconcile
1. The baseline is restored after the cleanup and the value survives the reboot
1. `harvester-node-manager-webhook` is `PreferDualStack` with an IPv4 and an IPv6 IP

### Cluster B: VM with IPv6 through cloud-init
1. Without IPv6 configuration the pod has an IPv4 and an IPv6 address, the guest has only IPv4 (no global IPv6 address, no IPv6 default route). This is the documented KubeVirt difference, not a Harvester bug
1. With the user data the VMI lists both addresses (for example `["10.52.0.99","fd52::63"]`), the guest has `fd10:0:2::2/120` and an IPv6 default route via `fd10:0:2::1`
1. The VM is reachable over IPv6 (ping, SSH, HTTP) and can reach the nodes over IPv6
1. The configuration is restored after a stop and start
1. On VLAN and overlay networks the result is recorded per network type

### Negative scenarios
1. Every request in the table is rejected with the listed message and the previous value is kept
