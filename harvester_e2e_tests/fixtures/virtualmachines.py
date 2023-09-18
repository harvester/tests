from io import StringIO
from time import sleep
from datetime import datetime, timedelta
from contextlib import contextmanager

import pytest
from paramiko import SSHClient, RSAKey, MissingHostKeyPolicy
from paramiko.ssh_exception import ChannelException


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

                pkey = RSAKey.from_private_key(StringIO(self.pkey)) if self.pkey else None

                cli = SSHClient()
                cli.set_missing_host_key_policy(MissingHostKeyPolicy())
                kws = dict(username=self.username, password=self.password, pkey=pkey, sock=ch)
                kws.update(kwargs)
                cli.connect(ipaddr, port, **kws)

                self._client = cli

            return self

        def close(self):
            if self.client and self.client.get_transport():
                self.client.close()
                self._client = None

        def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False, env=None):
            _, out, err = self.client.exec_command(command, bufsize, timeout, get_pty, env)
            return out.read().decode(), err.read().decode()

    return VMShell


@pytest.fixture(scope="session")
def vm_shell_from_host(vm_shell, host_shell, wait_timeout):
    @contextmanager
    def vm_login_from_host(
        host_ip, vm_ip, username, password=None, pkey=None, wait_timeout=wait_timeout
    ):
        with host_shell.login(host_ip, jumphost=True) as h:
            vm_sh = vm_shell(username, password, pkey)
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, jumphost=h.client)
                except ChannelException as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {vm_ip}") from login_ex

            with vm_sh as sh:
                yield sh

    return vm_login_from_host


@pytest.fixture(scope="session")
def vm_checker(api_client, wait_timeout):
    def _cb(code, data):
        return True

    class VMChecker:
        def __init__(self, vm_api, wait_timeout, snooze=3):
            self.vms = vm_api
            self.wait_timeout = wait_timeout
            self.snooze = snooze

        def _endtime(self):
            return datetime.now() + timedelta(seconds=self.wait_timeout)

        def wait_stopped(self, vm_name, endtime=None, callback=_cb, **kws):
            code, data = self.vms.stop(vm_name)
            if 204 != code:
                return False, (code, data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                code, data = self.vms.get_status(vm_name)
                if 404 == code and _cb(code, data):
                    break
                sleep(self.snooze)
            else:
                return False, (code, data)
            return True, (code, data)

        def wait_deleted(self, vm_name, endtime=None, callback=_cb, **kws):
            self.vms.delete(vm_name)
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                code, data = api_client.vms.get_status(vm_name)
                if 404 == code:
                    break
                sleep(self.snooze)
            else:
                return False, (code, data)
            return True, (code, data)

        def wait_started(self, vm_name, endtime=None, callback=_cb, **kws):
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                code, data = self.vms.get_status(vm_name, **kws)
                if (
                    200 == code
                    and "Running" == data.get('status', {}).get('phase')
                    and _cb(code, data)
                ):
                    break
                sleep(self.snooze)
            else:
                return False, (code, data)
            return True, (code, data)

        def wait_agent_connected(self, vm_name, endtime=None, callback=_cb, **kws):
            def cb_(code, data):
                conds = data.get('status', {}).get('conditions', [{}])
                return (
                    "AgentConnected" == conds[-1].get('type')
                    and _cb(code, data)
                )

            return self.wait_started(vm_name, endtime, cb_, **kws)

        def wait_interfaces(self, vm_name, endtime=None, callback=_cb, **kws):
            def cb_(code, data):
                return (
                    data.get('status', {}).get('interfaces')
                    and _cb(code, data)
                )
            return self.wait_agent_connected(vm_name, endtime, callback, **kws)

        def wait_cloudinit_done(self, shell, endtime=None, callback=_cb, **kws):
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                out, err = shell.exec_command('cloud-init status')
                if 'done' in out and _cb(out, err):
                    break
                sleep(self.snooze)
            else:
                return False, (out, err)
            return True, (out, err)

        def wait_migrated(self, vm_name, new_host, endtime=None, callback=_cb, **kws):
            code, data = self.vms.migrate(vm_name, new_host)
            if 204 != code:
                return False, (code, data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                code, data = self.vms.get_status(vm_name)
                migrating = data['metadata']['annotations'].get("harvesterhci.io/migrationState")
                if not migrating and new_host == data['status']['nodeName'] and _cb(code, data):
                    break
                sleep(self.snooze)
            else:
                return False, (code, data)
            return True, (code, data)

    return VMChecker(api_client.vms, wait_timeout)
