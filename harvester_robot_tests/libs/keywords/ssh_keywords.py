"""
SSH Keywords - general purpose shell access for tests.

Deliberately resource-agnostic: any test that needs to run a command on a
Harvester node, or inside a VM, uses these keywords. VMs are only reachable
from the node hosting them (they have a pod-network IP), so
`execute_command_in_vm` resolves the VM's IP and its node automatically and
tunnels through that node.
"""
import os
import sys
from datetime import datetime, timedelta
from time import sleep

# Add the path to the utility module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))) # noqa E402
from utility.utility import logging, get_retry_count_and_interval # noqa E402
from utility.ssh import ( # noqa E402
    DEFAULT_LOGIN_TIMEOUT, generate_ssh_keypair, shell, shell_via_jumphost
)
from vm import VM # noqa E402
from host import Host # noqa E402


class ssh_keywords:
    """Generic SSH keywords"""

    def __init__(self):
        self.vm = VM()
        self.host = Host()
        _, self.retry_interval = get_retry_count_and_interval()
        # Credentials used to reach the Harvester nodes themselves. They are
        # only needed as a jump host, so they default to the stock Harvester
        # node account and can be overridden per environment.
        self.node_username = os.getenv("HARVESTER_NODE_SSH_USER", "rancher")
        self.node_password = os.getenv("HARVESTER_NODE_SSH_PASSWORD") or None
        self.node_private_key = os.getenv("HARVESTER_NODE_SSH_PRIVATE_KEY") or None

    def generate_ssh_keypair(self):
        """Generate an RSA keypair.

        Returns a dict with `public_key` (OpenSSH, for cloud-init) and
        `private_key` (PEM, for logging in).
        """
        public_key, private_key = generate_ssh_keypair()
        return {"public_key": public_key, "private_key": private_key}

    def get_vm_ip_address(self, vm_name, network="default"):
        """Return the IP address the VM reports on the given network."""
        return self.vm.get_ip_address(vm_name, network)

    def get_vm_node_ip(self, vm_name):
        """Return the IP of the Harvester node currently hosting the VM."""
        node_name = self.vm.get_node_name(vm_name)
        return self.host.get_node_ip(node_name)

    def execute_command_on_host(self, host_ip, command, username=None,
                                password=None, private_key=None,
                                timeout=DEFAULT_LOGIN_TIMEOUT):
        """Run a command on a Harvester node and return its stdout."""
        with shell(host_ip,
                   username or self.node_username,
                   password if password is not None else self.node_password,
                   private_key or self.node_private_key,
                   timeout=int(timeout)) as sh:
            return sh.check_command(command)

    def execute_command_in_vm(self, vm_name, command, vm_user, private_key,
                              network="default", check=True,
                              timeout=DEFAULT_LOGIN_TIMEOUT):
        """Run a command inside a VM and return its stdout.

        Logs in through the node hosting the VM, since the VM's
        management-network IP is not routable from outside the cluster.
        Set check=False to tolerate a non-zero exit code.
        """
        with self._vm_shell(vm_name, vm_user, private_key,
                            network, timeout) as sh:
            if check:
                return sh.check_command(command)
            return sh.exec_command(command).stdout

    def wait_for_cloud_init_done(self, vm_name, vm_user, private_key,
                                 network="default",
                                 timeout=DEFAULT_LOGIN_TIMEOUT):
        """Wait until cloud-init has finished inside the VM.

        Commands issued before this can observe a half-configured VM.
        """
        with self._vm_shell(vm_name, vm_user, private_key,
                            network, timeout) as sh:
            result = sh.wait_for_command('cloud-init status', 'done',
                                         timeout=int(timeout))
            logging(f"cloud-init on {vm_name}: {result.stdout.strip()}")
            return result.stdout

    def execute_command_in_vm_and_expect_output(
            self, vm_name, command, vm_user, private_key, expected_output,
            network="default", timeout=DEFAULT_LOGIN_TIMEOUT):
        """Retry `command` in a VM until its stdout equals `expected_output`.

        A VM does not observe a change the instant the API reports it -- the
        kernel may still be bringing resources online after a restart -- so
        polling is needed rather than a single read. Comparison is done on
        the stripped stdout.
        """
        expected = str(expected_output).strip()
        with self._vm_shell(vm_name, vm_user, private_key,
                            network, timeout) as sh:
            endtime = datetime.now() + timedelta(seconds=int(timeout))
            actual = None
            while datetime.now() < endtime:
                actual = sh.exec_command(command).stdout.strip()
                if actual == expected:
                    logging(f"VM {vm_name}: {command!r} returned {actual!r}")
                    return actual
                sleep(self.retry_interval)

        raise AssertionError(
            f"VM {vm_name}: {command!r} did not return {expected!r} within "
            f"{timeout}s (last output: {actual!r})")

    def _vm_shell(self, vm_name, vm_user, private_key, network, timeout):
        """Context manager: shell inside `vm_name`, via its hosting node.

        VMs authenticate by key only -- the test cloud images have
        password authentication disabled.
        """
        vm_ip = self.get_vm_ip_address(vm_name, network)
        host_ip = self.get_vm_node_ip(vm_name)
        logging(f"Opening shell to VM {vm_name} ({vm_ip}) via node {host_ip}")

        return shell_via_jumphost(
            jump_ip=host_ip,
            jump_username=self.node_username,
            jump_password=self.node_password,
            jump_pkey=self.node_private_key,
            target_ip=vm_ip,
            target_username=vm_user,
            target_pkey=private_key,
            timeout=int(timeout),
        )
