from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import datetime
from subprocess import run, PIPE

import pytest
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


@pytest.fixture(scope='class')
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
        yield Path(f.name)
