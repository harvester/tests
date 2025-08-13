import re
from io import StringIO
from time import sleep
from datetime import datetime, timedelta
from ipaddress import ip_network
from contextlib import contextmanager

import pytest
from paramiko import SSHClient, RSAKey, MissingHostKeyPolicy
from paramiko.ssh_exception import ChannelException, NoValidConnectionsError


@pytest.fixture(scope="session")
def vm_mgmt_static(api_client):
    code, data = api_client.hosts.get()
    assert 200 == code, (code, data)

    for node in data['data']:
        rke2_args = node['metadata']['annotations']['rke2.io/node-args']
        match = re.search(r'cluster-cidr[\",]+((?:\d+\.?)+\/\d+)\"', rke2_args)
        if match:
            cluster_cidr = match.group(1)
            break
    else:
        raise AssertionError("cluster-cidr is not available")

    mgmt_network = ip_network(cluster_cidr)
    mgmt_route = {
        "gateway": "10.0.2.1",
        "netmask": f"{mgmt_network.netmask}",
        "network": f"{mgmt_network.network_address}"
    }
    return dict(type="static", address="10.0.2.2/24", routes=[mgmt_route])


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
                except (ChannelException, NoValidConnectionsError) as e:
                    login_ex = e
                    sleep(3)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {vm_ip}") from login_ex

            yield vm_sh

    return vm_login_from_host


@pytest.fixture(scope="session")
def vm_checker(api_client, wait_timeout, sleep_timeout, vm_shell):
    from dataclasses import dataclass, field

    @dataclass
    class ResponseContext:
        callee: str
        code: int
        data: dict
        options: dict = field(default_factory=dict, compare=False)

        def __iter__(self):
            ''' handy method be used to unpack'''
            return iter([self.code, self.data])

    @dataclass
    class ShellContext:
        command: str
        stdout: str
        stderr: str
        options: dict = field(default_factory=dict, compare=False)

        def __iter__(self):
            ''' handy method be used to unpack'''
            return iter([self.stdout, self.stderr])

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
            ''' context manager to temporarily change snooze or wait_timeout '''
            s, t = self.snooze, self.wait_timeout
            try:
                self.snooze, self.wait_timeout = snooze or s, wait_timeout or t
                yield self
            finally:
                self.snooze, self.wait_timeout = s, t

        def wait_getable(self, vm_name, endtime=None, callback=default_cb, **kws):
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get', *self.vms.get(vm_name, **kws))
                if 200 == ctx.code and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, ctx
            return True, ctx

        def wait_stopped(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.stop', *self.vms.stop(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, ctx

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('get_status', *self.vms.get_status(vm_name, **kws))
                if 404 == ctx.code and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, ctx
            return True, ctx

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

        def wait_status_running(self, vm_name, endtime=None, callback=default_cb, **kws):
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get', *self.vms.get(vm_name, **kws))
                status = ctx.data.get('status', {}).get('printableStatus')
                if 200 == ctx.code and "Running" == status and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, ctx
            return True, ctx

        def wait_deleted(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.delete', *self.vms.delete(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, ctx

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
                if 404 == ctx.code and callback(ctx):
                    break
                sleep(self.snooze)
            else:
                return False, ctx
            return True, ctx

        def wait_restarted(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, ctx

            options = dict(old_pods=set(ctx.data['status']['activePods'].items()))
            ctx = ResponseContext('vm.restart', *self.vms.restart(vm_name, **kws), options)
            if 404 == ctx.code and callback(ctx):
                return False, ctx

            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                ctx = ResponseContext('vm.get_status', *self.vms.get_status(vm_name, **kws),
                                      ctx.options)
                if 404 != ctx.code:
                    old_pods = ctx.options['old_pods']
                    cur_pods = ctx.data['status'].get('activePods', {}).items()
                    if old_pods.difference(cur_pods or old_pods) and callback(ctx):
                        break
                sleep(self.snooze)
            else:
                return False, ctx
            return self.wait_started(vm_name, endtime, callback, **kws)

        def wait_started(self, vm_name, endtime=None, callback=default_cb, **kws):
            ctx = ResponseContext('vm.start', *self.vms.start(vm_name, **kws))
            if 404 == ctx.code and callback(ctx):
                return False, ctx

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
                return False, ctx
            return True, ctx

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

        def wait_ip_addresses(self, vm_name, ifnames, endtime=None, callback=default_cb, **kws):
            def cb(ctx):
                if ctx.callee == 'vm.start':
                    return callback(ctx)
                ifaces = {d['name']: d for d in ctx.data.get('status', {}).get('interfaces', {})
                          if 'name' in d}
                return (
                    all(ifaces.get(name, {}).get('ipAddress') for name in ifnames)
                    and callback(ctx)
                )

            ifnames = list(ifnames)
            return self.wait_interfaces(vm_name, endtime, cb, **kws)

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
                return False, ctx

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
                return False, ctx
            return True, ctx

        def wait_ssh_connected(
            self, vm_ip, username, password=None, pkey=None, endtime=None, **kws
        ):
            vm_sh = vm_shell(username, password, pkey)
            endtime = endtime or self._endtime()
            while endtime > datetime.now():
                try:
                    vm_sh.connect(vm_ip, **kws)
                except (ChannelException, NoValidConnectionsError) as e:
                    login_ex = e
                    sleep(self.snooze)
                else:
                    break
            else:
                raise AssertionError(f"Unable to login to VM {vm_ip}") from login_ex

            return vm_sh

    return VMChecker(api_client.vms, wait_timeout, sleep_timeout)


@pytest.fixture(scope="session")
def vm_calc():
    from re import match
    from json import loads

    class VMResourceCalc:
        UNITS = ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
        FRACTIONAL = ('', 'm', 'u', 'n', 'p', 'f', 'a', 'z', 'y')

        @classmethod
        def node_resources(cls, node, *, res_types=('cpu', 'memory')):
            reserved = loads(node['metadata']['annotations']["management.cattle.io/pod-requests"])
            reserved = {k: cls.parse_unit(v) for k, v in reserved.items() if k in res_types}
            available = node['status']['allocatable']
            available = {k: cls.parse_unit(v) for k, v in available.items() if k in res_types}
            schedulable = {k: v - reserved[k] for k, v in available.items()}
            return {
                'schedulable': schedulable,
                'available': available,
                'reserved': reserved
            }

        @classmethod
        def format_unit(
            cls, value, *, increment=1000, start_exp=0, min_exp=0, max_exp=99, max_precision=2,
            suffix='', add_suffix=True, suffix_space=True, first_suffix=None, can_round_0=True
        ):
            # type: (int, int, int, int, int, int) -> str
            # https://github.com/harvester/dashboard/blob/master/shell/utils/units.js#L4

            val, exp, divide = value, start_exp, max_exp >= 0

            if divide:
                while exp < min_exp or (val >= increment and exp + 1 < len(cls.UNITS)
                                        and exp < max_exp):
                    val = val / increment
                    exp += 1
            else:
                while exp < (min_exp * -1) or (val < increment and exp + 1 < len(cls.FRACTIONAL)
                                               and exp < (max_exp * -1)):
                    val = val * increment
                    exp += 1

            if val < 10 and max_precision >= 1:
                rv = f"{round(val * (10 ** max_precision) / (10 ** max_precision))}"
            else:
                rv = f"{round(val)}"

            if rv == '0' and not can_round_0 and value != 0:
                val, exp = value, 0
                while val >= increment:
                    val /= increment
                    exp += 1
                return cls.format_unit(
                    val, increment=increment, start_exp=start_exp, min_exp=exp, max_exp=exp,
                    max_precision=max_precision, suffix=suffix, add_suffix=add_suffix,
                    suffix_space=suffix_space, first_suffix=first_suffix
                )

            if add_suffix:
                rv = f"{rv} " if suffix_space else rv
                if exp == 0 and first_suffix is not None:
                    rv += f"{first_suffix}"
                else:
                    rv += f"{cls.UNITS[exp] if divide else cls.FRACTIONAL[exp]}{suffix}"

            return rv

        @classmethod
        def parse_unit(cls, value):
            # https://github.com/harvester/dashboard/blob/master/shell/utils/units.js#L83
            try:
                pattern = r"^([0-9.-]+)\s*([^0-9.-]?)([^0-9.-]?)"
                val, unit, inc = match(pattern, value).groups()
                val = float(val)
                assert unit != ""
            except AttributeError:
                raise ValueError("Could not parse the value", value)
            except (AssertionError, ValueError):
                return val

            # µ (mu) symbol -> u
            unit = 'u' if ord(unit[0]) == 181 else unit

            divide = unit in cls.FRACTIONAL
            multiply = unit.upper() in cls.UNITS
            inc_base = 1024 if inc == 'i' and (divide or multiply) else 1000

            if divide:
                exp = cls.FRACTIONAL.index(unit)
                return val / (inc_base ** exp)

            if multiply:
                exp = cls.UNITS.index(unit.upper())
                return val * (inc_base ** exp)

    return VMResourceCalc
