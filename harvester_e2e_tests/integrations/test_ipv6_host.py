"""Host level IPv6 state must follow the install-time IP family choice.

Covers harvester/harvester#10755, #10795, #10796 (dual-stack IPv4-first) and the
1.9 -> 1.10 upgrade fix (harvester-installer#1298, harvester#11309, harvester#12143).

Source of truth is `install.ipfamilies` in /oem/harvester.config on each node:
  * absent / ["IPv4"]      -> IPv4-only: kernel IPv6 disabled, no global IPv6 address
  * ["IPv4", "IPv6"]       -> dual-stack: kernel IPv6 enabled, mgmt bridge has SLAAC/DHCPv6
                              address, node podCIDRs hold one IPv4 and one IPv6 range

The same tests are valid on a fresh install and after an upgrade from 1.9.
"""
import ipaddress

import pytest
import yaml

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]

NODE_INTERNAL_IP_ANNOTATION = "rke2.io/internal-ip"
HARVESTER_CONFIG = "/oem/harvester.config"
SYSCTL_DROPIN = "/etc/sysctl.d/zz-harvester-enable-ipv6.conf"
UPGRADE_OVERRIDE = "/oem/91_ipv6_sysctl.yaml"
MGMT_BRIDGE = "mgmt-br"
SYSCTL_KEYS = (
    "net.ipv6.conf.all.disable_ipv6",
    "net.ipv6.conf.default.disable_ipv6",
    "net.ipv6.conf.lo.disable_ipv6",
)


def ipv6_enabled_from_config(config_text):
    """True only when install.ipfamilies contains IPv6; missing/empty means IPv4-only."""
    data = yaml.safe_load(config_text or "") or {}
    families = (data.get("install") or {}).get("ipfamilies") or []
    return "IPv6" in families


def parse_sysctl_dropin(text):
    """Parse `key = value` lines of a sysctl drop-in, ignoring comments."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")) or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def global_ipv6_addresses(ip_addr_output):
    """Global-scope IPv6 addresses from `ip -6 -o addr show` output."""
    found = []
    for line in ip_addr_output.splitlines():
        fields = line.split()
        if "inet6" not in fields:
            continue
        addr = ipaddress.ip_interface(fields[fields.index("inet6") + 1]).ip
        if not (addr.is_link_local or addr.is_loopback or addr.is_multicast):
            found.append(addr)
    return found


def node_ips(node):
    """Addresses from the rke2.io/internal-ip annotation, e.g. "10.0.0.5,fd00::5"."""
    raw = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]
    return [ipaddress.ip_address(i.strip()) for i in raw.split(",") if i.strip()]


def ssh_ip(node):
    """IPv4 address used for SSH (dual-stack nodes list IPv4 first, then IPv6)."""
    return str(next(a for a in node_ips(node) if a.version == 4))


def pod_cidr_families(pod_cidrs):
    return sorted(ipaddress.ip_network(c, strict=False).version for c in pod_cidrs)


class TestIPv6Helpers:
    """Offline checks of the parsing helpers, no cluster needed."""

    def test_node_ips_dual_stack_annotation(self):
        node = {"metadata": {"annotations": {
            NODE_INTERNAL_IP_ANNOTATION: "192.168.103.237,fd00:cafe:4::1a8"}}}
        assert [a.version for a in node_ips(node)] == [4, 6]
        assert ssh_ip(node) == "192.168.103.237"

    def test_ssh_ip_ipv4_only_annotation(self):
        node = {"metadata": {"annotations": {NODE_INTERNAL_IP_ANNOTATION: "10.0.0.5"}}}
        assert ssh_ip(node) == "10.0.0.5"

    @pytest.mark.parametrize("text,expected", [
        ("", False),
        ("install:\n  mode: create\n", False),
        ("install:\n  ipfamilies: []\n", False),
        ("install:\n  ipfamilies: [IPv4]\n", False),
        ("install:\n  ipfamilies: [IPv4, IPv6]\n", True),
        ("install:\n  ipfamilies:\n  - IPv4\n  - IPv6\n", True),
    ])
    def test_ipv6_enabled_from_config(self, text, expected):
        assert ipv6_enabled_from_config(text) is expected

    def test_parse_sysctl_dropin(self):
        text = ("# Written by harvester-installer (dual-stack install)\n"
                + "".join(f"{k} = 0\n" for k in SYSCTL_KEYS))
        assert parse_sysctl_dropin(text) == {k: "0" for k in SYSCTL_KEYS}

    def test_global_ipv6_addresses_skips_link_local(self):
        out = (
            "5: mgmt-br    inet6 fd00:1::5a/64 scope global dynamic \\ valid_lft 85000sec\n"
            "5: mgmt-br    inet6 fe80::1/64 scope link \\ valid_lft forever\n"
        )
        assert [str(a) for a in global_ipv6_addresses(out)] == ["fd00:1::5a"]
        assert global_ipv6_addresses("") == []

    def test_pod_cidr_families(self):
        assert pod_cidr_families(["10.52.0.0/24", "fd52::/64"]) == [4, 6]
        assert pod_cidr_families(["10.52.0.0/24"]) == [4]


@pytest.fixture(scope="module")
def nodes(api_client):
    code, data = api_client.hosts.get()
    assert 200 == code, (code, data)
    assert data["data"], "No nodes found"
    return data["data"]


def _run(shell, command):
    out, err = shell.exec_command(command)
    return out.strip(), err.strip()


def ipv6_state_failures(nodes, host_shell):
    """Per node: config, sysctl runtime + drop-in, bridge address and NM profile agree.

    Returns a list of human readable mismatches (empty when everything is consistent).
    """
    failures = []
    for node in nodes:
        ip = ssh_ip(node)
        name = node["metadata"]["name"]
        with host_shell.login(ip) as sh:
            cfg, _ = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
            enabled = ipv6_enabled_from_config(cfg)
            want = "0" if enabled else "1"

            # runtime kernel state
            for key in SYSCTL_KEYS:
                out, err = _run(sh, f"sudo sysctl -n {key}")
                if out != want:
                    failures.append(f"{name}: {key}={out!r}, want {want!r} {err}")

            # persisted drop-in, rewritten on every boot (also after upgrade)
            dropin, _ = _run(sh, f"sudo cat {SYSCTL_DROPIN}")
            parsed = parse_sysctl_dropin(dropin)
            for key in SYSCTL_KEYS:
                if parsed.get(key) != want:
                    failures.append(f"{name}: {SYSCTL_DROPIN} {key}="
                                    f"{parsed.get(key)!r}, want {want!r}")

            # the upgrade override exists only for IPv4-only nodes upgraded from 1.9;
            # it must never be left behind on a dual-stack node
            if enabled:
                out, _ = _run(sh, f"sudo test -e {UPGRADE_OVERRIDE} && echo present")
                if out == "present":
                    failures.append(f"{name}: stale {UPGRADE_OVERRIDE} on dual-stack node")

            # management bridge
            addrs_out, _ = _run(sh, f"ip -6 -o addr show dev {MGMT_BRIDGE} scope global")
            addrs = global_ipv6_addresses(addrs_out)
            if enabled and not addrs:
                failures.append(f"{name}: no global IPv6 address on {MGMT_BRIDGE}")
            if not enabled and addrs:
                failures.append(f"{name}: unexpected IPv6 {addrs} on {MGMT_BRIDGE}")

            # NetworkManager profile of the bridge
            method, _ = _run(
                sh,
                "sudo nmcli -g ipv6.method connection show "
                f"\"$(sudo nmcli -t -f NAME,DEVICE connection show --active "
                f"| awk -F: '$2==\"{MGMT_BRIDGE}\"{{print $1; exit}}')\"")
            want_method = "auto" if enabled else "disabled"
            if method != want_method:
                failures.append(f"{name}: NM ipv6.method={method!r}, want {want_method!r}")

    return failures


@pytest.mark.hosts
@pytest.mark.p0
class TestHostIPv6:
    def test_ipv6_matches_install_choice(self, nodes, host_shell):
        failures = ipv6_state_failures(nodes, host_shell)
        assert not failures, "\n".join(failures)

    def test_node_pod_cidrs_follow_ip_family(self, nodes, host_shell):
        """API view: dual-stack nodes get one IPv4 and one IPv6 pod CIDR, IPv4-only just IPv4."""
        failures = []
        for node in nodes:
            ip = ssh_ip(node)
            with host_shell.login(ip) as sh:
                cfg, _ = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
            want = [4, 6] if ipv6_enabled_from_config(cfg) else [4]
            families = sorted(a.version for a in node_ips(node))
            if families != want:
                failures.append(f"{node['metadata']['name']}: internal-ip annotation "
                                f"families={families}, want {want}")
            cidrs = node.get("spec", {}).get("podCIDRs") or []
            if pod_cidr_families(cidrs) != want:
                failures.append(
                    f"{node['metadata']['name']}: podCIDRs={cidrs}, want families {want}")
        assert not failures, "\n".join(failures)

    def test_cluster_is_homogeneous(self, nodes, host_shell):
        """All nodes must share the same IP family choice (mixed clusters are unsupported)."""
        modes = set()
        for node in nodes:
            ip = ssh_ip(node)
            with host_shell.login(ip) as sh:
                cfg, _ = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
            modes.add(ipv6_enabled_from_config(cfg))
        assert len(modes) == 1, "Nodes disagree on dual-stack vs IPv4-only"
