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
def harvester_metadata(pytestconfig):
    ''' be used to store harvester's metadata and expose into html report. '''
    # ref: https://github.com/pytest-dev/pytest-html/blob/4.1.1/src/pytest_html/basereport.py#L71
    try:
        from pytest_metadata.plugin import metadata_key
        metadata = pytestconfig.stash[metadata_key]
    except ImportError:
        metadata = pytestconfig._metadata

    harv = dict()
    metadata["Harvester"] = harv
    return harv


@pytest.fixture(scope="session")
def api_client(request, harvester_metadata):
    endpoint = request.config.getoption("--endpoint")
    username = request.config.getoption("--username")
    password = request.config.getoption("--password")
    ssl_verify = request.config.getoption("--ssl_verify", False)

    api = HarvesterAPI(endpoint)
    api.authenticate(username, password, verify=ssl_verify)

    api.session.verify = ssl_verify
    api.load_managers(api.cluster_version)

    harvester_metadata['Cluster Endpoint'] = endpoint
    harvester_metadata['Cluster Version'] = api.raw_version

    return api


@pytest.fixture(scope="session")
def wait_timeout(request):
    return request.config.getoption("--wait-timeout", 300)


@pytest.fixture(scope="session")
def sleep_timeout(request):
    return request.config.getoption("--sleep-timeout", 4)


@pytest.fixture(scope="session")
def upgrade_timeout(request):
    return request.config.getoption('--upgrade-wait-timeout') or 7200


@pytest.fixture(scope="session")
def rancher_wait_timeout(request):
    return request.config.getoption("--rancher-cluster-wait-timeout", 1800)


@pytest.fixture(scope="session")
def ubuntu_checksum(request):
    """Returns Ubuntu checksum from config"""
    return request.config.getoption("--ubuntu-checksum")


@pytest.fixture(scope="session")
def opensuse_checksum(request):
    """Returns openSUSE checksum from config"""
    return request.config.getoption("--opensuse-checksum")


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
        key_size=4096,
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
def skip_if_version(request, api_client):
    ''' To mark test case should be skip when hit the condition string.

    Args:
        *args: Version string prefixing with one of operators: `!=`, `==`, `>=`, `<=`, `>`, `<`
    Keyword Args:
        reason: The reason string for `pytest.skip`
        condition: Condition callable function to check compare result(bool), default is `all`
    '''
    mark = request.node.get_closest_marker("skip_if_version")
    if mark:
        cluster_ver = api_client.cluster_version
        return _action_if_version(cluster_ver, mark, pytest.skip)


@pytest.fixture(autouse=True)
def xfail_if_version(request, api_client):
    ''' To mark test case should be xfail when hit the condition string.

    Args:
        *args: Version string prefixing with one of operators: `!=`, `==`, `>=`, `<=`, `>`, `<`
    Keyword Args:
        reason: The reason string for `pytest.xfail`
        condition: Condition callable function to check compare result(bool), default is `all`
    '''
    mark = request.node.get_closest_marker("xfail_if_version")
    if mark:
        cluster_ver = api_client.cluster_version
        return _action_if_version(cluster_ver, mark, pytest.xfail)


def _action_if_version(cluster_ver, mark, pytest_act: Callable):
    base_reason = "Cluster version {cluster_ver} matches {cond} condition(s) in {versions}"
    extra_reason = mark.kwargs.get('reason', "")
    reason = f"{base_reason}. {extra_reason}" if extra_reason else base_reason
    checks = [_version_check(vstr, cluster_ver) for vstr in mark.args]
    cond = mark.kwargs.get('condition', all)

    if cond(r for *_, r in checks):
        versions = [f"{op} {v}" for op, v, _ in checks]
        return pytest_act(
            reason.format(cluster_ver=cluster_ver, cond=cond.__name__, versions=versions)
        )


def _version_check(vstring, version):
    from operator import le, lt, ge, gt, ne, eq
    ops = {"<=": le, "<": lt, ">=": ge, ">": gt, "!=": ne, "==": eq}

    try:
        op = target_ver = None
        op, target_ver = re.search(r"([<>=!]+)\s?(.+)", vstring).groups()
        return op, target_ver, ops[op](version, parse_version(target_ver))
    except Exception:
        return op, target_ver, False


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

        def login(self, ipaddr, port=22, jumphost=False, allow_agent=False,
                  look_for_keys=False, **kwargs):
            if not self.client:
                cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=self.pkey)
                kws.update(kwargs)

                # in case we're using a password to log into the host, this
                # prevents paramiko from getting confused by ssh keys in the ssh
                # agent:
                if self.password and not self.pkey:
                    kws.update(dict(allow_agent=allow_agent,
                                    look_for_keys=look_for_keys))

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
    # TODO: Try to redesign refer to multiprocessing package (e.g. apply_async and map_async)
    def _polling_for(subject: str,
                     checker: Callable[..., bool],
                     poller: Callable, *args,
                     timeout=wait_timeout):
        """ Polling expected confition for `timeout`s every `sleep_timeout`s

        Arguments:
          subject: str, what is waiting for
          checker: Callable, check `poller` output and returns bool
          args: list, [*poller_args, testee]
          poller: Callable, poller(*poller_args, testee) for each testee

        Returns:
          Any: `poller` output if qualified by `checker`

        Raises:
          AssertionError: if still NOT qualified within `timeout`s
        """
        *poller_args, testee = args
        testees = testee if isinstance(testee, list) else [testee]
        checker_args_len = len(getfullargspec(checker).args)

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            for testee in testees[:]:
                output = poller(*poller_args, testee)
                # unpack poller output according to checker signature
                qualified = checker(*output) if checker_args_len > 1 else checker(output)
                if qualified:
                    testees.remove(testee)
            if not testees:
                return output
            sleep(sleep_timeout)
        else:
            raise AssertionError(
                f'Timeout {timeout}s waiting for {subject}\n'
                f'Got error: {output}'
            )

    return _polling_for
