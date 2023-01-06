import re
from io import StringIO
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import datetime
from subprocess import run, PIPE

import pytest
from paramiko import SSHClient, RSAKey, MissingHostKeyPolicy
from pkg_resources import parse_version
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import asymmetric, serialization

from harvester_api import HarvesterAPI


@pytest.fixture(scope="session")
def api_client(request):
    endpoint = request.config.getoption("--endpoint")
    username = request.config.getoption("--username")
    password = request.config.getoption("--password")
    ssl_verify = request.config.getoption("--ssl_verify", False)

    api = HarvesterAPI(endpoint)
    api.authenticate(username, password, verify=ssl_verify)

    api.session.verify = ssl_verify

    return api


@pytest.fixture(scope="session")
def wait_timeout(request):
    return request.config.getoption('--wait-timeout', 300)


@pytest.fixture(scope="session")
def host_state(request):
    class HostState:
        files = ("power_off.sh", "power_on.sh", "reboot.sh")  # [False, True, -1]

        def __init__(self, script_path, delay=120):
            self.path = Path(script_path)
            self.delay = delay

        def __repr__(self):
            return f"HostState({self.path}, {self.delay})"

        def power(self, name, ip, on=True):
            proc = run([self.path / self.files[on], name, ip],
                       stdout=PIPE, stderr=PIPE)
            return proc.returncode, proc.stdout, proc.stderr

        def reboot(self, name, ip):
            return self.power(name, ip, -1)

    return HostState(request.config.getoption("--node-scripts-location"))


@pytest.fixture(scope='module')
def unique_name():
    return datetime.now().strftime("%m-%d-%Hh%Mm%Ss%f")


@pytest.fixture(scope="class")
def ssh_keypair():
    private_key = asymmetric.rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=backends.default_backend()
    )
    private_key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.OpenSSH,
        serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_key_ssh = public_key.public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    return public_key_ssh.decode('utf-8'), private_key_pem.decode('utf-8')


@pytest.fixture(scope="session")
def fake_image_file():
    with NamedTemporaryFile("wb") as f:
        f.seek(10 * 1024 ** 2 - 1)  # 10MB
        f.write(b"\0")
        f.seek(0)
        yield Path(f.name)


@pytest.fixture(scope="session")
def support_bundle_state():
    class SupportBundle:
        def __init__(self, fio):
            self.uid = ""
            self.files = list()  # for checking file name
            self.fio = fio  # for checking file content

    with NamedTemporaryFile() as f:
        yield SupportBundle(f)


@pytest.fixture(scope="session")
def expected_settings():
    return {
        "1.1.0": {'storage-network', 'containerd-registry', 'ui-plugin-index'},
        "default": {
            'additional-ca',
            'auto-disk-provision-paths',
            'backup-target',
            'cluster-registration-url',
            'http-proxy',
            'log-level',
            'overcommit-config',
            'release-download-url',
            'server-version',
            'ssl-certificates',
            'ssl-parameters',
            'support-bundle-image',
            'support-bundle-namespaces',
            'support-bundle-timeout',
            'ui-index',
            'ui-source',
            'upgrade-checker-enabled',
            'upgrade-checker-url',
            'vip-pools',
            'vm-force-reset-policy',
        }
    }


@pytest.fixture(autouse=True)
def skip_version_before(request, api_client):
    mark = request.node.get_closest_marker("skip_version_before")
    if mark and parse_version(mark.args[0]) > api_client.cluster_version:
        pytest.skip(
            f"Cluster Version `{api_client.cluster_version}` is not included"
            f" in the supported version (most >= `{mark.args[0]}`)"
        )


@pytest.fixture(autouse=True)
def skip_version_after(request, api_client):
    mark = request.node.get_closest_marker("skip_version_after")
    if mark and parse_version(mark.args[0]) <= api_client.cluster_version:
        pytest.skip(
            f"Cluster Version `{api_client.cluster_version}` is not included"
            f" in the supported version (most < `{mark.args[0]}`)"
        )


@pytest.fixture(scope="session")
def host_shell(request):
    password = request.config.getoption("--host-password") or None
    pkey = request.config.getoption('--host-private-key') or None
    if pkey:
        pkey = RSAKey.from_private_key(StringIO(pkey))

    class HostShell:
        _client = _jump = None

        def __init__(self, username, password=None, pkey=None):
            self.username = username
            self.password = password
            self.pkey = pkey

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.logout()

        @property
        def client(self):
            return self._client

        def login(self, ipaddr, port=22, jumphost=False, **kwargs):
            if not self.client:
                self._client = cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=self.pkey)
                kws.update(kwargs)
                cli.connect(ipaddr, port, **kws)

                if jumphost:
                    self.jumphost_policy()
                    self._jump = True

            return self

        def logout(self):
            if self.client and self.client.get_transport():
                if self._jump:
                    self.jumphost_policy(False)
                    self._jump = None
                self.client.close()
                self._client = None

        def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, env=None):
            _, out, err = self.client.exec_command(command, bufsize, timeout, get_pty, env)
            return out.read().decode(), err.read().decode()

        def jumphost_policy(self, allow=True):
            ctx, err = self.exec_command("sudo cat /etc/ssh/sshd_config")
            if allow:
                renew = re.sub(r'\n(Allow(?:Tcp|Agent)Forwarding no)',
                               lambda m: f"\n#{m.group(1)}", ctx, re.I | re.M)
            else:
                renew = re.sub(r'#(Allow(?:Tcp|Agent)Forwarding no)',
                               lambda m: m.group(1), ctx, re.I | re.M)
            self.exec_command(f'sudo cat<<"EOF">_config\n{renew}EOF')
            self.exec_command('sudo mv _config /etc/ssh/sshd_config'
                              ' && sudo systemctl restart sshd')

    return HostShell('rancher', password, pkey)
