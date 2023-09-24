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
def vm_checker(request, api_client, wait_timeout, sleep_timeout):
    from dataclasses import dataclass, field

    @dataclass
    class ResponseContext:
        callee: str
        code: int
        data: dict
        options: dict = field(default_factory=dict, compare=False)

    @dataclass
    class ShellContext:
        command: str
        stdout: str
        stderr: str
        options: dict = field(default_factory=dict, compare=False)

    def default_cb(ctx):
        ''' identity callback function for adjust checking condition.

        :rtype: boolean
        :return: True when hit the additional check
        '''

        return True

    class VMChecker:
        def __init__(self, vm_api, wait_timeout, snooze=3):
            self.vms = vm_api
            self.wait_timeout = wait_timeout
            self.snooze = snooze

        def _endtime(self):
            return datetime.now() + timedelta(seconds=self.wait_timeout)

        @contextmanager
        def configure(self, snooze=None, wait_timeout=None):
            s, t = self.snooze, self.wait_timeout
            try:
                self.snooze, self.wait_timeout = snooze or s, wait_timeout or t
                yield self
            finally:
                self.snooze, self.wait_timeout = s, t

        def wait_stopped(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.stop', *self.vms.stop(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('get_status', *self.vms.get_status(vm_name, **kws))
                if 404 == ctx.code and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.code, ctx.data)
            return True, (ctx.code, ctx.data)

        def wait_status_stopped(self, vm_name, endtime=None, callback=default_cb, **kws):
            def cb(ctx):
                if ctx.callee == 'vm.stop':
                    return callback(ctx)
                ctx.code, ctx.data = self.vms.get(vm_name, **kws)
                ctx.callee = 'vm.get'
                return (
                    200 == ctx.code
                    and "Stopped" == ctx.data.get('status', {}).get('printableStatus')
                    and callback(ctx)
                )
            return self.wait_stopped(vm_name, endtime, cb, **kws)

        def wait_deleted(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.delete', *self.vms.delete(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
                if 404 == ctx.code and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.code, ctx.data)
            return True, (ctx.code, ctx.data)

        def wait_restarted(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            options = dict(old_pods=set(ctx.data['status']['activePods'].items()))
            ctx = ResponseContext('vm.restart', *self.vms.restart(vm_name, **kws), options)
            if 204 != ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws),
                                      ctx.options)
                old_pods = ctx.options['old_pods']
                cur_pods = ctx.data['status'].get('activePods', {}).items()
                if old_pods.difference(cur_pods or old_pods) and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.code, ctx.data)
            return self.wait_started(vm_name, endtime, callback, **kws)

        def wait_started(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.start', *self.vms.start(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
                if (
                    200 == ctx.code
                    and "Running" == ctx.data.get('status', {}).get('phase')
                    and callback(ctx)
                ):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.code, ctx.data)
            return True, (ctx.code, ctx.data)

        def wait_agent_connected(self, vm_name, endtime=None, callback=default_cb, **kws):
            def cb(ctx):
                if ctx.callee == 'vm.start':
                    return callback(ctx)

                conds = ctx.data.get('status', {}).get('conditions', [{}])
                return (
                    "AgentConnected" == conds[-1].get('type')
                    and callback(ctx)
                )

            return self.wait_started(vm_name, endtime, cb, **kws)

        def wait_interfaces(self, vm_name, endtime=None, callback=default_cb, **kws):
            def cb(ctx):
                if ctx.callee == 'vm.start':
                    return callback(ctx)

                return (
                    ctx.data.get('status', {}).get('interfaces')
                    and callback(ctx)
                )
            return self.wait_agent_connected(vm_name, endtime, cb, **kws)

        def wait_cloudinit_done(self, shell, endtime=None, callback=default_cb, **kws):
            cmd = 'cloud-init status'
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ShellContext(cmd, *shell.exec_command(cmd))
                if 'done' in ctx.stdout and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.stdout, ctx.stderr)
            return True, (ctx.stdout, ctx.stderr)

        def wait_migrated(self, vm_name, new_host, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.migrate', *self.vms.migrate(vm_name, new_host, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, (ctx.code, ctx.data)

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
                if (
                    not ctx.data['metadata']['annotations'].get("harvesterhci.io/migrationState")
                    and new_host == ctx.data['status']['nodeName']
                    and callback(ctx)
                ):
                    break
                sleep(self.snooze)
            else:
                return False, (ctx.code, ctx.data)
            return True, (ctx.code, ctx.data)

    return VMChecker(api_client.vms, wait_timeout, sleep_timeout)
