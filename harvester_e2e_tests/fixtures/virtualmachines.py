from io import StringIO

import pytest
from paramiko import SSHClient, RSAKey, MissingHostKeyPolicy


@pytest.fixture(scope="session")
def vm_shell():
    class VMShell:
        _client = _jump = None

        def __init__(self, username, password=None, pkey=None):
            self.username = username
            self.password = password
            self.pkey = pkey

        @classmethod
        def login(cls, ipaddr, username, password=None, pkey=None, port=22, jumphost=None, **kws):
            obj = cls(username, password, pkey)
            obj.connect(ipaddr, port, jumphost, **kws)
            return obj

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.close()

        @property
        def client(self):
            return self._client

        def connect(self, ipaddr, port=22, jumphost=None, **kwargs):
            if not self.client:
                if jumphost:
                    tp = jumphost.get_transport()
                    ch = tp.open_channel('direct-tcpip', (ipaddr, port), tp.sock.getpeername())
                else:
                    ch = None

                if self.pkey:
                    pkey = RSAKey.from_private_key(StringIO(self.pkey))

                self._client = cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=pkey, sock=ch)
                kws.update(kwargs)
                cli.connect(ipaddr, port, **kws)
            return self

        def close(self):
            if self.client and self.client.get_transport():
                self.client.close()
                self._client = None

        def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, env=None):
            _, out, err = self.client.exec_command(command, bufsize, timeout, get_pty, env)
            return out.read().decode(), err.read().decode()

    return VMShell
