import re
from datetime import datetime, timedelta
from io import StringIO
from tempfile import NamedTemporaryFile
from pathlib import Path
from subprocess import run, PIPE
from typing import Callable
from time import sleep
from inspect import getfullargspec

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
    return request.config.getoption("--wait-timeout", 300)


@pytest.fixture(scope="session")
def sleep_timeout(request):
    return request.config.getoption("--sleep-timeout", 4)


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
    """Default unique name"""
    return datetime.now().strftime("%Hh%Mm%Ss%f-%m-%d")


@pytest.fixture(scope='module')
def gen_unique_name():
    """Generate unique name on-demand"""
    return lambda: datetime.now().strftime("%Hh%Mm%Ss%f-%m-%d")


@pytest.fixture(scope="module")
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
    if mark:
        cluster_ver = api_client.cluster_version
        for target_ver in mark.args:
            if '-head' not in cluster_ver.public and parse_version(target_ver) > cluster_ver:
                return pytest.skip(
                    f"Cluster Version `{api_client.cluster_version}` is not included"
                    f" in the supported version (most >= `{target_ver}`)"
                )


@pytest.fixture(autouse=True)
def skip_version_after(request, api_client):
    mark = request.node.get_closest_marker("skip_version_after")
    if mark:
        cluster_ver = api_client.cluster_version
        for target_ver in mark.args:
            if not hasattr(cluster_ver, 'major') or parse_version(target_ver) <= cluster_ver:
                return pytest.skip(
                    f"Cluster Version `{api_client.cluster_version}` is not included"
                    f" in the supported version (most < `{target_ver}`)"
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

        def reconnect(self, ipaddr, port=22, **kwargs):
            if self.client:
                self.client.close()
                self._client = cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=self.pkey)
                kws.update(kwargs)
                cli.connect(ipaddr, port, **kws)

        def login(self, ipaddr, port=22, jumphost=False, **kwargs):
            if not self.client:
                cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=self.pkey)
                kws.update(kwargs)
                cli.connect(ipaddr, port, **kws)
                self._client = cli

                if jumphost:
                    self.jumphost_policy()
                    self._jump = True
                    self.reconnect(ipaddr, port, **kws)

            return self

        def logout(self):
            if self.client and self.client.get_transport():
                if self._jump:
                    self.jumphost_policy(False)
                    self._jump = None
                self.client.close()
                self._client = None

        def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, env=None,
                         splitlines=False):
            _, out, err = self.client.exec_command(command, bufsize, timeout, get_pty, env)
            out, err = out.read().decode(), err.read().decode()
            if splitlines:
                out = out.splitlines()
            return out, err

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


@pytest.fixture(scope="session")
def polling_for(wait_timeout, sleep_timeout):
    def _polling_for(subject: str,
                     tester: Callable[..., bool],
                     testee: Callable, *testee_args, **testee_kwargs):
        """ Polling expected confition for `wait_timeout`s every `sleep_timeout`s

        Arguments:
          subject: what is waiting for
          tester: Callable which accepts `testee` output and returns bool
          testee: Callable returns output for `tester` to validate

        Returns:
          Any: `testee` output if qualified by `tester`

        Raises:
          AssertionError: if still NOT qualified by `tester` over `wait_timeout`
        """
        tester_args_len = len(getfullargspec(tester).args)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            output = testee(*testee_args, **testee_kwargs)
            # unpack output for tester according to its signature
            qualified = tester(*output) if tester_args_len > 1 else tester(output)
            if qualified:
                return output
            sleep(sleep_timeout)
        else:
            raise AssertionError(f'Timeout wait for {subject}\n{output}')

    return _polling_for
