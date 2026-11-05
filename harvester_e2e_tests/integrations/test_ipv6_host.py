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
import re

import pytest
import yaml

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]

NODE_INTERNAL_IP_ANNOTATION = "rke2.io/internal-ip"
HARVESTER_CONFIG = "/oem/harvester.config"
SYSCTL_DROPIN = "/etc/sysctl.d/zz-harvester-enable-ipv6.conf"
UPGRADE_OVERRIDE = "/oem/91_ipv6_sysctl.yaml"
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


def device_for_ipv4(ip_addr_output, address):
    """Interface holding `address`, from `ip -4 -o addr show` output (None if absent).

    The management address lives on `mgmt-br`, or on the VLAN device on top of it when
    the management network is tagged, so the device cannot be hardcoded.
    """
    for line in ip_addr_output.splitlines():
        fields = line.split()
        if "inet" not in fields:
            continue
        cidr = fields[fields.index("inet") + 1]
        if ipaddress.ip_interface(cidr).ip == ipaddress.ip_address(address):
            return fields[1].split("@")[0].rstrip(":")
    return None


def release_from_version(text):
    """(major, minor) of a server-version value, None for versionless dev builds."""
    match = re.search(r"v?(\d+)\.(\d+)", text or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def supports_ipv6_install_choice(api_client):
    """True when the cluster runs v1.10+ behavior (IPv6 follows install.ipfamilies).

    Reads the raw `server-version` setting on every call, so it reflects the cluster
    after an upgrade. `api_client.cluster_version` is cached and, for dev builds, can
    fall back to the KubeVirt version. Versionless values (master/hash builds) count
    as the newest release. Before v1.10 the installer enabled IPv6 on every host.
    """
    code, data = api_client.settings.get("server-version")
    assert 200 == code, (code, data)
    release = release_from_version(data.get("value", ""))
    return release is None or release >= (1, 10)


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

    @pytest.fixture
    def api_client(self):
        """Prevent the plugin's autouse version checks from contacting a cluster."""
        return None

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

    def test_device_for_ipv4(self):
        out = (
            "2: eth0    inet 169.254.1.1/16 scope link \\ valid_lft forever\n"
            "5: mgmt-br.100    inet 192.168.103.237/24 brd 192.168.103.255 scope global "
            "dynamic mgmt-br.100\\ valid_lft 3000sec\n"
        )
        assert device_for_ipv4(out, "192.168.103.237") == "mgmt-br.100"
        assert device_for_ipv4(out, "10.0.0.1") is None
        assert device_for_ipv4("", "10.0.0.1") is None

    @pytest.mark.parametrize("text,expected", [
        ("v1.9.0", (1, 9)),
        ("v1.9.10", (1, 9)),
        ("release-v1.9.0-rc5-b117-head", (1, 9)),
        ("v1.10-177462e7-head", (1, 10)),
        ("v1.10.0", (1, 10)),
        ("master-211c2b36-head", None),
        ("", None),
    ])
    def test_release_from_version(self, text, expected):
        assert release_from_version(text) == expected

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
    """Run a command and return stripped stdout, failing on any reported error.

    Discarding stderr would turn a failed read into an empty string, which then looks
    like an IPv4-only config or an empty address list and can satisfy the assertions.
    """
    out, err = shell.exec_command(command)
    assert not err.strip(), f"Failed to execute {command!r}: {err.strip()}"
    return out.strip()


def ipv6_state_failures(nodes, host_shell):
    """Per node: config, sysctl runtime + drop-in, bridge address and NM profile agree.

    Returns a list of human readable mismatches (empty when everything is consistent).
    """
    failures = []
    for node in nodes:
        ip = ssh_ip(node)
        name = node["metadata"]["name"]
        with host_shell.login(ip) as sh:
            cfg = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
            enabled = ipv6_enabled_from_config(cfg)
            want = "0" if enabled else "1"

            # runtime kernel state
            for key in SYSCTL_KEYS:
                out = _run(sh, f"sudo sysctl -n {key}")
                if out != want:
                    failures.append(f"{name}: {key}={out!r}, want {want!r}")

            # persisted drop-in, rewritten on every boot (also after upgrade)
            dropin = _run(sh, f"sudo cat {SYSCTL_DROPIN}")
            parsed = parse_sysctl_dropin(dropin)
            for key in SYSCTL_KEYS:
                if parsed.get(key) != want:
                    failures.append(f"{name}: {SYSCTL_DROPIN} {key}="
                                    f"{parsed.get(key)!r}, want {want!r}")

            # the upgrade override exists only for IPv4-only nodes upgraded from 1.9;
            # it must never be left behind on a dual-stack node
            if enabled:
                out = _run(sh, f"sudo test -e {UPGRADE_OVERRIDE} && echo present")
                if out == "present":
                    failures.append(f"{name}: stale {UPGRADE_OVERRIDE} on dual-stack node")

            # management device: mgmt-br, or its VLAN device on a tagged management network
            mgmt_dev = device_for_ipv4(_run(sh, "ip -4 -o addr show"), ip)
            if not mgmt_dev:
                failures.append(f"{name}: no interface holds the management address {ip}")
                continue

            addrs_out = _run(sh, f"ip -6 -o addr show dev {mgmt_dev} scope global")
            addrs = global_ipv6_addresses(addrs_out)
            if enabled and not addrs:
                failures.append(f"{name}: no global IPv6 address on {mgmt_dev}")
            if not enabled and addrs:
                failures.append(f"{name}: unexpected IPv6 {addrs} on {mgmt_dev}")

            # NetworkManager profile of the management device
            method = _run(
                sh,
                "sudo nmcli -g ipv6.method connection show "
                f"\"$(sudo nmcli -t -f NAME,DEVICE connection show --active "
                f"| awk -F: '$2==\"{mgmt_dev}\"{{print $1; exit}}')\"")
            want_method = "auto" if enabled else "disabled"
            if method != want_method:
                failures.append(f"{name}: NM ipv6.method={method!r}, want {want_method!r}")

    return failures


@pytest.mark.hosts
@pytest.mark.p0
class TestHostIPv6:
    @pytest.fixture(autouse=True)
    def require_install_choice(self, api_client):
        """v1.9 intentionally enables IPv6 on IPv4-only hosts, the checks start at v1.10."""
        if not supports_ipv6_install_choice(api_client):
            pytest.skip("IPv6 follows install.ipfamilies only from v1.10")

    def test_ipv6_matches_install_choice(self, nodes, host_shell):
        failures = ipv6_state_failures(nodes, host_shell)
        assert not failures, "\n".join(failures)

    def test_node_pod_cidrs_follow_ip_family(self, nodes, host_shell):
        """API view: dual-stack nodes get one IPv4 and one IPv6 pod CIDR, IPv4-only just IPv4."""
        failures = []
        for node in nodes:
            ip = ssh_ip(node)
            with host_shell.login(ip) as sh:
                cfg = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
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
                cfg = _run(sh, f"sudo cat {HARVESTER_CONFIG}")
            modes.add(ipv6_enabled_from_config(cfg))
        assert len(modes) == 1, "Nodes disagree on dual-stack vs IPv4-only"
