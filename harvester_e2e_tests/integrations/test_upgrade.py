import re
import json
import yaml
import socket
from time import sleep
from operator import add
from functools import reduce
from datetime import datetime, timedelta

import pytest
from paramiko.ssh_exception import SSHException, NoValidConnectionsError
from harvester_api.managers import DEFAULT_HARVESTER_NAMESPACE, DEFAULT_LONGHORN_NAMESPACE

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.virtualmachines"
]

UPGRADE_STATE_LABEL = "harvesterhci.io/upgradeState"
NODE_INTERNAL_IP_ANNOTATION = "rke2.io/internal-ip"


@pytest.fixture(scope="module")
def cluster_state(request, unique_name, api_client):
    class ClusterState:
        vm1 = None
        vm2 = None
        vm3 = None
        pass

    state = ClusterState()

    if request.config.getoption('--upgrade-target-version'):
        state.version_verify = True
        state.version = request.config.getoption('--upgrade-target-version')
    else:
        state.version_verify = False
        state.version = f"version-{unique_name}"

    return state


@pytest.fixture(scope="module")
def harvester_crds():
    return {
        "addons.harvesterhci.io": False,
        "blockdevices.harvesterhci.io": False,
        "keypairs.harvesterhci.io": False,
        "preferences.harvesterhci.io": False,
        "settings.harvesterhci.io": False,
        "supportbundles.harvesterhci.io": False,
        "upgrades.harvesterhci.io": False,
        "versions.harvesterhci.io": False,
        "virtualmachinebackups.harvesterhci.io": False,
        "virtualmachineimages.harvesterhci.io": False,
        "virtualmachinerestores.harvesterhci.io": False,
        "virtualmachinetemplates.harvesterhci.io": False,
        "virtualmachinetemplateversions.harvesterhci.io": False,

        "clusternetworks.network.harvesterhci.io": False,
        "linkmonitors.network.harvesterhci.io": False,
        "nodenetworks.network.harvesterhci.io": False,
        "vlanconfigs.network.harvesterhci.io": False,
        "vlanstatuses.network.harvesterhci.io": False,

        "ksmtuneds.node.harvesterhci.io": False,

        "loadbalancers.loadbalancer.harvesterhci.io": False,
    }


@pytest.fixture(scope="module")
def upgrade_target(request, unique_name):
    version = request.config.getoption('--upgrade-target-version')
    version = version or f"upgrade-{unique_name}"
    iso_url = request.config.getoption('--upgrade-iso-url')
    assert iso_url, "Target ISO URL should not be empty"
    checksum = request.config.getoption("--upgrade-iso-checksum")
    assert checksum, "Checksum for Target ISO should not be empty"

    return version, iso_url, checksum


@pytest.fixture(scope="module")
def image(api_client, image_ubuntu, unique_name, wait_timeout):
    unique_image_id = f'image-{unique_name}'
    code, data = api_client.images.create_by_url(
        unique_image_id, image_ubuntu.url, display_name=f"{unique_name}-{image_ubuntu.name}"
    )

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_image_id)
        if 100 == data.get('status', {}).get('progress', 0):
            break
        sleep(3)
    else:
        raise AssertionError(
            "Failed to create Image with error:\n"
            f"Status({code}): {data}"
        )

    yield dict(id=f"{data['metadata']['namespace']}/{unique_image_id}",
               user=image_ubuntu.ssh_user)

    code, data = api_client.images.delete(unique_image_id)


@pytest.fixture(scope='module')
def cluster_network(vlan_nic, api_client, unique_name):
    code, data = api_client.clusternetworks.get_config()
    assert 200 == code, (code, data)

    node_key = 'network.harvesterhci.io/matched-nodes'
    cnet_nodes = dict()  # cluster_network: items
    for cfg in data['items']:
        if vlan_nic in cfg['spec']['uplink']['nics']:
            nodes = json.loads(cfg['metadata']['annotations'][node_key])
            cnet_nodes.setdefault(cfg['spec']['clusterNetwork'], []).extend(nodes)

    code, data = api_client.hosts.get()
    assert 200 == code, (code, data)
    all_nodes = set(n['id'] for n in data['data'])
    try:
        # vlad_nic configured on specific cluster network, reuse it
        yield next(cnet for cnet, nodes in cnet_nodes.items() if all_nodes == set(nodes))
        return None
    except StopIteration:
        configured_nodes = reduce(add, cnet_nodes.values(), [])
        if any(n in configured_nodes for n in all_nodes):
            raise AssertionError(
                "Not all nodes' VLAN NIC {vlan_nic} are available.\n"
                f"VLAN NIC configured nodes: {configured_nodes}\n"
                f"All nodes: {all_nodes}\n"
            )

    # Create cluster network
    cnet = f"cnet-{datetime.strptime(unique_name, '%Hh%Mm%Ss%f-%m-%d').strftime('%H%M%S')}"
    created = []
    code, data = api_client.clusternetworks.create(cnet)
    assert 201 == code, (code, data)
    while all_nodes:
        node = all_nodes.pop()
        code, data = api_client.clusternetworks.create_config(node, cnet, vlan_nic, hostname=node)
        assert 201 == code, (
            f"Failed to create cluster config for {node}\n"
            f"Created: {created}\t Remaining: {all_nodes}\n"
            f"API Status({code}): {data}"
        )
        created.append(node)

    yield cnet

    # Teardown
    deleted = {name: api_client.clusternetworks.delete_config(name) for name in created}
    failed = [(name, code, data) for name, (code, data) in deleted.items() if 200 != code]
    if failed:
        fmt = "Unable to delete VLAN Config {} with error ({}): {}"
        raise AssertionError(
            "\n".join(fmt.format(name, code, data) for (name, code, data) in failed)
        )

    code, data = api_client.clusternetworks.delete(cnet)
    assert 200 == code, (code, data)


@pytest.fixture(scope="module")
def vm_network(api_client, unique_name, wait_timeout, cluster_network, vlan_id, cluster_state):
    code, data = api_client.networks.create(
        unique_name, vlan_id, cluster_network=cluster_network
    )
    assert 201 == code, (code, data)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.networks.get(unique_name)
        annotations = data['metadata'].get('annotations', {})
        if 200 == code and annotations.get('network.harvesterhci.io/route'):
            route = json.loads(annotations['network.harvesterhci.io/route'])
            if route['cidr']:
                break
        sleep(3)
    else:
        raise AssertionError(
            "VM network created but route info not available\n"
            f"API Status({code}): {data}"
        )

    cluster_state.network = data
    yield dict(name=unique_name, cidr=route['cidr'], namespace=data['metadata']['namespace'])

    code, data = api_client.networks.delete(unique_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.networks.get(unique_name)
        if 404 == code:
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to remote VM network {unique_name} after {wait_timeout}s\n"
            f"API Status({code}): {data}"
        )


@pytest.fixture(scope="module")
def config_storageclass(request, api_client, unique_name, cluster_state):
    replicas = request.config.getoption('--upgrade-sc-replicas') or 3

    code, default_sc = api_client.scs.get_default()
    assert 200 == code, (code, default_sc)

    sc_name = f"new-sc-{replicas}-{unique_name}"
    code, data = api_client.scs.create(sc_name, replicas)
    assert 201 == code, (code, data)

    code, data = api_client.scs.set_default(sc_name)
    assert 200 == code, (code, data)

    cluster_state.scs = (default_sc, data)
    yield default_sc, data

    code, data = api_client.scs.set_default(default_sc['metadata']['name'])
    assert 200 == code, (code, data)


@pytest.fixture(scope="module")
def interceptor(api_client):
    from inspect import getmembers, ismethod

    class Interceptor:
        _v121_vm = True

        def intercepts(self):
            meths = getmembers(self, predicate=ismethod)
            return [m for name, m in meths if name.startswith("intercept_")]

        def check(self, data):
            for func in self.intercepts():
                func(data)

        def intercept_v121_vm(self, data):
            if "v1.2.1" != api_client.cluster_version.raw:
                return
            if self._v121_vm:
                code, data = api_client.vms.get()
                for vm in data.get('data', []):
                    api_client.vms.stop(vm['metadata']['name'])
                self._v121_vm = False
            else:
                conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
                st = data.get('metadata', {}).get('labels', {}).get('harvesterhci.io/upgradeState')
                if "Succeeded" == st and "True" == conds.get('Completed', {}).get('status'):
                    code, data = api_client.vms.get()
                    for vm in data.get('data', []):
                        api_client.vms.start(vm['metadata']['name'])

    return Interceptor()


@pytest.fixture(scope="class")
def config_backup_target(request, api_client, wait_timeout):
    # multiple fixtures from `vm_backup_restore`
    conflict_retries = 5
    nfs_endpoint = request.config.getoption('--nfs-endpoint')
    assert nfs_endpoint, f"NFS endpoint not configured: {nfs_endpoint}"
    assert nfs_endpoint.startswith("nfs://"), (
        f"NFS endpoint should starts with `nfs://`, not {nfs_endpoint}"
    )
    backup_type, config = ("NFS", dict(endpoint=nfs_endpoint))

    code, data = api_client.settings.get('backup-target')
    origin_spec = api_client.settings.BackupTargetSpec.from_dict(data)

    spec = getattr(api_client.settings.BackupTargetSpec, backup_type)(**config)
    # ???: when switching S3 -> NFS, update backup-target will easily hit resource conflict
    # so we would need retries to apply the change.
    for _ in range(conflict_retries):
        code, data = api_client.settings.update('backup-target', spec)
        if 409 == code and "Conflict" == data['reason']:
            sleep(3)
        else:
            break
    else:
        raise AssertionError(
            f"Unable to update backup-target after {conflict_retries} retried."
            f"API Status({code}): {data}"
        )
    assert 200 == code, (
        f'Failed to update backup target to {backup_type} with {config}\n'
        f"API Status({code}): {data}"
    )

    yield spec

    # remove unbound LH backupVolumes
    code, data = api_client.lhbackupvolumes.get()
    assert 200 == code, "Failed to list lhbackupvolumes"

    check_names = []
    for volume_data in data["items"]:
        volume_name = volume_data["metadata"]["name"]
        backup_name = volume_data["status"]["lastBackupName"]
        if not backup_name:
            api_client.lhbackupvolumes.delete(volume_name)
            check_names.append(volume_name)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        for name in check_names[:]:
            code, data = api_client.lhbackupvolumes.get(name)
            if 404 == code:
                check_names.remove(name)
        if not check_names:
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to delete unbound lhbackupvolumes: {check_names}\n"
            f"Last API Status({code}): {data}"
            )

    # restore to original backup-target and remove backups not belong to it
    code, data = api_client.settings.update('backup-target', origin_spec)
    code, data = api_client.backups.get()
    assert 200 == code, "Failed to list backups"

    check_names = []
    for backup in data['data']:
        endpoint = backup['status']['backupTarget'].get('endpoint')
        if endpoint != origin_spec.value.get('endpoint'):
            api_client.backups.delete(backup['metadata']['name'])
            check_names.append(backup['metadata']['name'])

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        for name in check_names[:]:
            code, data = api_client.backups.get(name)
            if 404 == code:
                check_names.remove(name)
        if not check_names:
            break
        sleep(3)
    else:
        raise AssertionError(
            f"Failed to delete backups: {check_names}\n"
            f"Last API Status({code}): {data}"
            )


@pytest.fixture
def stopped_vm(request, api_client, ssh_keypair, wait_timeout, unique_name, image):
    unique_vm_name = f"{request.node.name.lstrip('test_').replace('_', '-')}-{unique_name}"
    cpu, mem = 1, 2
    pub_key, pri_key = ssh_keypair
    vm_spec = api_client.vms.Spec(cpu, mem)
    vm_spec.add_image("disk-0", image['id'])
    vm_spec.run_strategy = "Halted"

    userdata = yaml.safe_load(vm_spec.user_data)
    userdata['ssh_authorized_keys'] = [pub_key]
    vm_spec.user_data = yaml.dump(userdata)

    code, data = api_client.vms.create(unique_vm_name, vm_spec)
    assert 201 == code, (code, data)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get(unique_vm_name)
        if "Stopped" == data.get('status', {}).get('printableStatus'):
            break
        sleep(1)

    yield unique_vm_name, image['user'], pri_key

    code, data = api_client.vms.get(unique_vm_name)
    vm_spec = api_client.vms.Spec.from_dict(data)

    api_client.vms.delete(unique_vm_name)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.vms.get_status(unique_vm_name)
        if 404 == code:
            break
        sleep(3)

    for vol in vm_spec.volumes:
        vol_name = vol['volume']['persistentVolumeClaim']['claimName']
        api_client.volumes.delete(vol_name)


@pytest.mark.upgrade
@pytest.mark.negative
@pytest.mark.any_nodes
class TestInvalidUpgrade:
    def test_iso_url(self, api_client, unique_name, upgrade_timeout):
        """
        Steps:
        1. Create an invalid manifest.
        2. Try to upgrade with the invalid manifest.
        3. Upgrade should not start and fail.
        """
        version, url, checksum = unique_name, "https://invalid_iso_url", 'not_a_valid_checksum'

        code, data = api_client.versions.get(version)
        if code != 200:
            code, data = api_client.versions.create(version, url, checksum)
            assert code == 201, f"Failed to create invalid version: {data}"

        code, data = api_client.upgrades.create(version)
        assert code == 201, f"Failed to create invalid upgrade: {data}"

        endtime = datetime.now() + timedelta(seconds=upgrade_timeout)
        while endtime > datetime.now():
            code, data = api_client.upgrades.get(data['metadata']['name'])
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            verified = [
                "False" == conds.get('Completed', {}).get('status'),
                "False" == conds.get('ImageReady', {}).get('status'),
                "retry limit" in conds.get('ImageReady', {}).get('message', "")
            ]
            if all(verified):
                break
        else:
            raise AssertionError(f"Upgrade NOT failed in expected conditions: {conds}")

        # teardown
        api_client.upgrades.delete(data['metadata']['name'])
        api_client.versions.delete(version)

    @pytest.mark.parametrize(
        "resort", [slice(None, None, -1), slice(None, None, 2)], ids=("mismatched", "invalid")
    )
    def test_checksum(self, api_client, unique_name, upgrade_target, upgrade_timeout, resort):
        if resort.step == 2:
            pytest.skip("issue: https://github.com/harvester/harvester/issues/5480")

        version, url, checksum = upgrade_target
        version = f"{version}-{unique_name}"

        code, data = api_client.versions.create(version, url, checksum[resort])
        assert 201 == code, f"Failed to create upgrade for {version}"
        code, data = api_client.upgrades.create(version)
        assert 201 == code, f"Failed to start upgrade for {version}"

        endtime = datetime.now() + timedelta(seconds=upgrade_timeout)
        while endtime > datetime.now():
            code, data = api_client.upgrades.get(data['metadata']['name'])
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            verified = [
                "False" == conds.get('Completed', {}).get('status'),
                "False" == conds.get('ImageReady', {}).get('status'),
                "n't match the file actual check" in conds.get('ImageReady', {}).get('message', "")
            ]
            if all(verified):
                break
        else:
            raise AssertionError(f"Upgrade NOT failed in expected conditions: {conds}")

        # teardown
        api_client.upgrades.delete(data['metadata']['name'])
        api_client.versions.delete(version)

    @pytest.mark.skip("https://github.com/harvester/harvester/issues/5494")
    def test_version_compatibility(
        self, api_client, unique_name, upgrade_target, upgrade_timeout
    ):
        version, url, checksum = upgrade_target
        version = f"{version}-{unique_name}"

        code, data = api_client.versions.create(version, url, checksum)
        assert 201 == code, f"Failed to create upgrade for {version}"
        code, data = api_client.upgrades.create(version)
        assert 201 == code, f"Failed to start upgrade for {version}"

        endtime = datetime.now() + timedelta(seconds=upgrade_timeout)
        while endtime > datetime.now():
            code, data = api_client.upgrades.get(data['metadata']['name'])
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            verified = []  # TODO
            if all(verified):
                break
        else:
            raise AssertionError(f"Upgrade NOT failed in expected conditions: {conds}")

        # teardown
        api_client.upgrades.delete(data['metadata']['name'])
        api_client.versions.delete(version)

    def test_degraded_volume(
        self, api_client, wait_timeout, vm_shell_from_host, vm_checker, upgrade_target, stopped_vm
    ):
        """
        Criteria: create upgrade should fails if there are any degraded volumes
        Steps:
        1. Create a VM using a volume with 3 replicas.
        2. Delete one replica of the volume. Let the volume stay in
           degraded state.
        3. Immediately upgrade Harvester.
        4. Upgrade should fail.
        """
        vm_name, ssh_user, pri_key = stopped_vm
        vm_started, (code, vmi) = vm_checker.wait_started(vm_name)
        assert vm_started, (code, vmi)

        # Write date into VM
        vm_ip = next(iface['ipAddress'] for iface in vmi['status']['interfaces']
                     if iface['name'] == 'default')
        code, data = api_client.hosts.get(vmi['status']['nodeName'])
        host_ip = next(addr['address'] for addr in data['status']['addresses']
                       if addr['type'] == 'InternalIP')
        with vm_shell_from_host(host_ip, vm_ip, ssh_user, pkey=pri_key) as sh:
            stdout, stderr = sh.exec_command(
                "dd if=/dev/urandom of=./generate_file bs=1M count=1024; sync"
            )
            assert not stdout, (stdout, stderr)

        # Get pv name of the volume
        claim_name = vmi["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"]
        code, data = api_client.volumes.get(name=claim_name)
        assert code == 200, f"Failed to get volume {claim_name}: {data}"
        pv_name = data["spec"]["volumeName"]

        # Make the volume becomes degraded
        code, data = api_client.lhreplicas.get()
        assert code == 200 and data['items'], f"Failed to get longhorn replicas ({code}): {data}"
        replica = next(r for r in data["items"] if pv_name == r['spec']['volumeName'])
        api_client.lhreplicas.delete(name=replica['metadata']['name'])
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.lhvolumes.get(pv_name)
            if 200 == code and "degraded" == data['status']['robustness']:
                break
        else:
            raise AssertionError(
                f"Unable to make the Volume {pv_name} degraded\n"
                f"API Status({code}): {data}"
            )

        # create upgrade and verify it is not allowed
        version, url, checksum = upgrade_target
        code, data = api_client.versions.create(version, url, checksum)
        assert code == 201, f"Failed to create version {version}: {data}"
        code, data = api_client.upgrades.create(version)
        assert code == 400, f"Failed to verify degraded volume: {code}, {data}"

        # Teardown invalid upgrade
        api_client.versions.delete(version)


@pytest.mark.upgrade
@pytest.mark.any_nodes
class TestAnyNodesUpgrade:
    @pytest.mark.dependency(name="preq_setup_logging")
    def test_preq_setup_logging(self, api_client):
        # TODO: enable addon if > v1.2.0
        return

    @pytest.mark.dependency(name="preq_setup_vmnetwork")
    def test_preq_setup_vmnetwork(self, vm_network):
        ''' Be used to trigger the fixture to setup VM network '''

    @pytest.mark.dependency(name="preq_setup_storageclass")
    def test_preq_setup_storageclass(self, config_storageclass):
        """ Be used to trigger the fixture to setup storageclass"""

    @pytest.mark.dependency(name="preq_setup_vms")
    def test_preq_setup_vms(
        self, api_client, ssh_keypair, unique_name, vm_checker, vm_shell, vm_network, image,
        config_storageclass, config_backup_target, wait_timeout, cluster_state
    ):
        # create new storage class, make it default
        # create 3 VMs:
        # - having the new storage class
        # - the VM that have some data written, take backup
        # - the VM restored from the backup
        pub_key, pri_key = ssh_keypair
        old_sc, new_sc = config_storageclass
        unique_vm_name = f"ug-vm-{unique_name}"

        cpu, mem, size = 1, 2, 5
        vm_spec = api_client.vms.Spec(cpu, mem, mgmt_network=False)
        vm_spec.add_image('disk-0', image['id'], size=size)
        vm_spec.add_network('nic-1', f"{vm_network['namespace']}/{vm_network['name']}")
        userdata = yaml.safe_load(vm_spec.user_data)
        userdata['ssh_authorized_keys'] = [pub_key]
        vm_spec.user_data = yaml.dump(userdata)

        code, data = api_client.vms.create(unique_vm_name, vm_spec)
        assert 201 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_interfaces(unique_vm_name)
        assert vm_got_ips, (
            f"Failed to Start VM({unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'nic-1')
        # write data into VM
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            try:
                with vm_shell.login(vm_ip, image['user'], pkey=pri_key) as sh:
                    cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
                    assert cloud_inited and not err, (out, err)
                    out, err = sh.exec_command(
                        "dd if=/dev/urandom of=./generate_file bs=1M count=1024; sync"
                    )
                    assert not out, (out, err)
                    vm1_md5, err = sh.exec_command(
                        "md5sum ./generate_file > ./generate_file.md5; cat ./generate_file.md5"
                    )
                    assert not err, (vm1_md5, err)
                    break
            except (SSHException, NoValidConnectionsError):
                sleep(5)
        else:
            raise AssertionError("Timed out while writing data into VM")

        # Take backup then check it's ready
        code, data = api_client.vms.backup(unique_vm_name, unique_vm_name)
        assert 204 == code, (code, data)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, backup = api_client.backups.get(unique_vm_name)
            if 200 == code and backup.get('status', {}).get('readyToUse'):
                break
            sleep(3)
        else:
            raise AssertionError(
                f'Timed-out waiting for the backup \'{unique_vm_name}\' to be ready.'
            )
        # restore into new VM
        restored_vm_name = f"r-{unique_vm_name}"
        spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(unique_vm_name, spec)
        assert 201 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_interfaces(restored_vm_name)
        assert vm_got_ips, (
            f"Failed to Start VM({restored_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )
        # Check data consistency
        r_vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                       if iface['name'] == 'nic-1')
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            try:
                with vm_shell.login(r_vm_ip, image['user'], pkey=pri_key) as sh:
                    cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
                    assert cloud_inited and not err, (out, err)
                    out, err = sh.exec_command("md5sum -c ./generate_file.md5")
                    assert not err, (out, err)
                    vm2_md5, err = sh.exec_command("cat ./generate_file.md5")
                    assert not err, (vm2_md5, err)
                    assert vm1_md5 == vm2_md5
                    out, err = sh.exec_command(
                        f"ping -c1 {vm_ip} > /dev/null && echo -n success || echo -n fail"
                    )
                    assert "success" == out and not err
                    break
            except (SSHException, NoValidConnectionsError):
                sleep(5)
        else:
            raise AssertionError("Unable to login to restored VM to check data consistency")

        # Create VM having additional volume with new storage class
        vm_spec.add_volume("vol-1", 5, storage_cls=new_sc['metadata']['name'])
        code, data = api_client.vms.create(f"sc-{unique_vm_name}", vm_spec)
        assert 201 == code, (code, data)
        vm_got_ips, (code, data) = vm_checker.wait_interfaces(f"sc-{unique_vm_name}")
        assert vm_got_ips, (
            f"Failed to Start VM(sc-{unique_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # store into cluster's state
        names = [unique_vm_name, f"r-{unique_vm_name}", f"sc-{unique_vm_name}"]
        cluster_state.vms = dict(md5=vm1_md5, names=names, ssh_user=image['user'], pkey=pri_key)

    @pytest.mark.dependency(name="any_nodes_upgrade")
    def test_perform_upgrade(
        self, api_client, unique_name, upgrade_target, upgrade_timeout, interceptor
    ):
        """
        - perform upgrade
        - check all nodes upgraded
        """
        # Check nodes counts
        code, data = api_client.hosts.get()
        assert code == 200, (code, data)
        nodes = len(data['data'])

        # create Upgrade version and start
        skip_version_check = {"harvesterhci.io/skip-version-check": True}  # for test purpose
        version, url, checksum = upgrade_target
        version = f"{version}-{unique_name}"
        code, data = api_client.versions.create(version, url, checksum)
        assert 201 == code, f"Failed to create upgrade for {version}"
        code, data = api_client.upgrades.create(version, annotations=skip_version_check)
        assert 201 == code, f"Failed to start upgrade for {version}"
        upgrade_name = data['metadata']['name']

        # Check upgrade status
        # TODO: check every upgrade stages
        endtime = datetime.now() + timedelta(seconds=upgrade_timeout * nodes)
        while endtime > datetime.now():
            code, data = api_client.upgrades.get(upgrade_name)
            if 200 != code:
                continue
            interceptor.check(data)
            conds = dict((c['type'], c) for c in data.get('status', {}).get('conditions', []))
            state = data.get('metadata', {}).get('labels', {}).get('harvesterhci.io/upgradeState')
            if "Succeeded" == state and "True" == conds.get('Completed', {}).get('status'):
                break
            if any("False" == c['status'] for c in conds.values()):
                raise AssertionError(f"Upgrade failed with conditions: {conds.values()}")
            sleep(30)
        else:
            raise AssertionError(
                f"Upgrade timed out with conditions: {conds.values()}\n"
                f"API Status({code}): {data}"
            )

    @pytest.mark.dependency(depends=["any_nodes_upgrade", "preq_setup_logging"])
    def test_verify_logging_pods(self, api_client):
        """ Verify logging pods and logs
        Criteria: https://github.com/harvester/tests/issues/535
        """

        code, pods = api_client.get_pods(namespace="cattle-logging-system")
        assert code == 200 and len(pods['data']) > 0, "No logging pods found"

        fails = []
        for pod in pods['data']:
            # Verify pod is running or completed
            phase = pod["status"]["phase"]
            if phase not in ("Running", "Succeeded"):
                fails.append((pod['metadata']['name'], phase))
        else:
            assert not fails, (
                "\n".join(f"Pod({n})'s phase({p}) is not expected." for n, p in fails)
            )

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_audit_log(self, api_client, host_shell, wait_timeout):
        code, data = api_client.hosts.get()
        assert 200 == code, (code, data)
        label_main = "node-role.kubernetes.io/control-plane"
        masters = [n for n in data['data'] if n['metadata']['labels'].get(label_main) == "true"]
        assert len(masters) > 0, "No master nodes found"

        script = ("sudo tail /var/lib/rancher/rke2/server/logs/audit.log | awk 'END{print}' "
                  "| jq .requestReceivedTimestamp "
                  "| xargs -I {} date -d \"{}\" +%s")

        node_ips = [n["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION] for n in masters]
        cmp = dict()
        done = set()
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            for ip in done.symmetric_difference(node_ips):
                try:
                    with host_shell.login(ip) as shell:
                        out, err = shell.exec_command(script)
                        timestamp = int(out)
                        if not err and ip not in cmp:
                            cmp[ip] = timestamp
                            continue
                        if not err and cmp[ip] < timestamp:
                            done.add(ip)
                except (SSHException, NoValidConnectionsError, socket.timeout):
                    continue

            if not done.symmetric_difference(node_ips):
                break
            sleep(5)
        else:
            raise AssertionError(
                "\n".join("Node {ip} audit log is not updated." for ip in set(node_ips) ^ done)
            )

    @pytest.mark.dependency(depends=["any_nodes_upgrade", "preq_setup_vmnetwork"])
    def test_verify_network(self, api_client, cluster_state):
        """ Verify cluster and VLAN networks
        - cluster network `mgmt` should exists
        - Created VLAN should exists
        """

        code, cnets = api_client.clusternetworks.get()
        assert code == 200, (
            "Failed to get Networks: %d, %s" % (code, cnets))

        assert len(cnets["items"]) > 0, ("No Networks found")

        assert any(n['metadata']['name'] == "mgmt" for n in cnets['items']), (
            "Cluster network mgmt not found")

        code, vnets = api_client.networks.get()
        assert code == 200, (f"Failed to get VLANs: {code}, {vnets}" % (code, vnets))
        assert len(vnets["items"]) > 0, ("No VLANs found")

        used_vlan = cluster_state.network['metadata']['name']
        assert any(used_vlan == n['metadata']['name'] for n in vnets['items']), (
            f"VLAN {used_vlan} not found")

    @pytest.mark.dependency(depends=["any_nodes_upgrade", "preq_setup_vms"])
    def test_verify_vms(self, api_client, cluster_state, vm_shell, vm_checker, wait_timeout):
        """ Verify VMs' state and data
        Criteria:
        - VMs should keep in running state
        - data in VMs should not lost
        """

        code, vmis = api_client.vms.get_status()
        assert code == 200 and len(vmis['data']), (code, vmis)

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            fails, ips = list(), dict()
            for name in cluster_state.vms['names']:
                code, data = api_client.vms.get_status(name)
                try:
                    assert 200 == code
                    assert "Running" == data['status']['phase']
                    assert data['status']['nodeName']
                    ips[name] = next(iface['ipAddress'] for iface in data['status']['interfaces']
                                     if iface['name'] == 'nic-1')
                except (AssertionError, TypeError, StopIteration, KeyError) as ex:
                    fails.append((name, (ex, code, data)))
            if not fails:
                break
        else:
            raise AssertionError("\n".join(
                f"VM {name} is not in expected state.\nException: {ex}\nAPI Status({code}): {data}"
                for (name, (ex, code, data)) in fails)
            )

        pri_key, ssh_user = cluster_state.vms['pkey'], cluster_state.vms['ssh_user']
        for name in cluster_state.vms['names'][:-1]:
            vm_ip = ips[name]
            endtime = datetime.now() + timedelta(seconds=wait_timeout)
            while endtime > datetime.now():
                try:
                    with vm_shell.login(vm_ip, ssh_user, pkey=pri_key) as sh:
                        out, err = sh.exec_command("md5sum -c ./generate_file.md5")
                        assert not err, (out, err)
                        md5, err = sh.exec_command("cat ./generate_file.md5")
                        assert not err, (md5, err)
                        assert md5 == cluster_state.vms['md5']
                        break
                except (SSHException, NoValidConnectionsError):
                    sleep(5)
            else:
                fails.append(f"Data in VM({name}, {vm_ip}) is inconsistent.")

        assert not fails, "\n".join(fails)

        # Teardown: remove all VMs
        for name in cluster_state.vms['names']:
            code, data = api_client.vms.get(name)
            spec = api_client.vms.Spec.from_dict(data)
            _ = vm_checker.wait_deleted(name)
            for vol in spec.volumes:
                vol_name = vol['volume']['persistentVolumeClaim']['claimName']
                api_client.volumes.delete(vol_name)

    @pytest.mark.dependency(depends=["any_nodes_upgrade", "preq_setup_vms"])
    def test_verify_restore_vm(
        self, api_client, cluster_state, vm_shell, vm_checker, wait_timeout
    ):
        """ Verify VM restored from the backup
        Criteria:
        - VM should able to start
        - data in VM should not lost
        """

        backup_name = cluster_state.vms['names'][0]
        restored_vm_name = f"new-r-{backup_name}"

        # Restore VM from backup and check networking is good
        restore_spec = api_client.backups.RestoreSpec.for_new(restored_vm_name)
        code, data = api_client.backups.restore(backup_name, restore_spec)
        assert code == 201, "Unable to restore backup {backup_name} after upgrade"
        vm_got_ips, (code, data) = vm_checker.wait_interfaces(restored_vm_name)
        assert vm_got_ips, (
            f"Failed to Start VM({restored_vm_name}) with errors:\n"
            f"Status: {data.get('status')}\n"
            f"API Status({code}): {data}"
        )

        # Check data in restored VM is consistent
        pri_key, ssh_user = cluster_state.vms['pkey'], cluster_state.vms['ssh_user']
        vm_ip = next(iface['ipAddress'] for iface in data['status']['interfaces']
                     if iface['name'] == 'nic-1')
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            try:
                with vm_shell.login(vm_ip, ssh_user, pkey=pri_key) as sh:
                    cloud_inited, (out, err) = vm_checker.wait_cloudinit_done(sh)
                    assert cloud_inited and not err, (out, err)
                    out, err = sh.exec_command("md5sum -c ./generate_file.md5")
                    assert not err, (out, err)
                    md5, err = sh.exec_command("cat ./generate_file.md5")
                    assert not err, (md5, err)
                    assert md5 == cluster_state.vms['md5']
                    break
            except (SSHException, NoValidConnectionsError):
                sleep(5)
        else:
            raise AssertionError("Unable to login to restored VM to check data consistency")

        # teardown: remove the VM
        code, data = api_client.vms.get(restored_vm_name)
        spec = api_client.vms.Spec.from_dict(data)
        _ = vm_checker.wait_deleted(restored_vm_name)
        for vol in spec.volumes:
            vol_name = vol['volume']['persistentVolumeClaim']['claimName']
            api_client.volumes.delete(vol_name)

    @pytest.mark.dependency(depends=["any_nodes_upgrade", "preq_setup_storageclass"])
    def test_verify_storage_class(self, api_client, cluster_state):
        """ Verify StorageClasses and defaults
        - `new_sc` should be settle as default
        - `longhorn` should exists
        """
        code, scs = api_client.scs.get()
        assert code == 200, ("Failed to get StorageClasses: %d, %s" % (code, scs))
        assert len(scs["items"]) > 0, ("No StorageClasses found")

        created_sc = cluster_state.scs[-1]['metadata']['name']
        names = {sc['metadata']['name']: sc['metadata'].get('annotations') for sc in scs['items']}
        assert "longhorn" in names
        assert created_sc in names
        assert "storageclass.kubernetes.io/is-default-class" in names[created_sc]
        assert "true" == names[created_sc]["storageclass.kubernetes.io/is-default-class"]

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_os_version(self, request, api_client, cluster_state, host_shell):
        # Verify /etc/os-release on all nodes
        script = "cat /etc/os-release"
        if not cluster_state.version_verify:
            pytest.skip("skip verify os version")

        # Get all nodes
        code, data = api_client.hosts.get()
        assert 200 == code, (code, data)
        for node in data['data']:
            node_ip = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]

            with host_shell.login(node_ip) as sh:
                lines, stderr = sh.exec_command(script, get_pty=True, splitlines=True)
                assert not stderr, (
                    f"Failed to execute {script} on {node_ip}: {stderr}")

                # eg: PRETTY_NAME="Harvester v1.1.0"
                assert cluster_state.version == re.findall(r"Harvester (.+?)\"", lines[3])[0], (
                    "OS version is not correct")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_rke2_version(self, api_client, host_shell):
        # Verify node version on all nodes
        script = "cat /etc/harvester-release.yaml"

        label_main = "node-role.kubernetes.io/control-plane"
        code, data = api_client.hosts.get()
        assert 200 == code, (code, data)
        masters = [n for n in data['data'] if n['metadata']['labels'].get(label_main) == "true"]

        # Verify rke2 version
        except_rke2_version = ""
        for node in masters:
            node_ip = node["metadata"]["annotations"][NODE_INTERNAL_IP_ANNOTATION]

            # Get except rke2 version
            if except_rke2_version == "":
                with host_shell.login(node_ip) as sh:
                    lines, stderr = sh.exec_command(script, get_pty=True, splitlines=True)
                    assert not stderr, (
                        f"Failed to execute {script} on {node_ip}: {stderr}")

                    for line in lines:
                        if "kubernetes" in line:
                            except_rke2_version = re.findall(r"kubernetes: (.*)", line.strip())[0]
                            break

                    assert except_rke2_version != "", ("Failed to get except rke2 version")

            assert node.get('status', {}).get('nodeInfo', {}).get(
                   "kubeletVersion", "") == except_rke2_version, (
                   "rke2 version is not correct")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_deployed_components_version(self, api_client):
        """ Verify deployed kubevirt and longhorn version
        Criteria:
        - except version(get from apps.catalog.cattle.io/harvester) should be equal to the version
          of kubevirt and longhorn
        """

        kubevirt_version_existed = False
        engine_image_version_existed = False
        longhorn_manager_version_existed = False

        # Get except version from apps.catalog.cattle.io/harvester
        code, apps = api_client.get_apps_catalog(name="harvester",
                                                 namespace=DEFAULT_HARVESTER_NAMESPACE)
        assert code == 200 and apps['type'] != "error", (
            f"Failed to get apps.catalog.cattle.io/harvester: {apps['message']}")

        # Get except image of kubevirt and longhorn
        kubevirt_operator = (
            apps['spec']['chart']['values']['kubevirt-operator']['containers']['operator'])
        kubevirt_operator_image = (
            f"{kubevirt_operator['image']['repository']}:{kubevirt_operator['image']['tag']}")

        longhorn = apps['spec']['chart']['values']['longhorn']['image']['longhorn']
        longhorn_images = {
            "engine-image": f"{longhorn['engine']['repository']}:{longhorn['engine']['tag']}",
            "longhorn-manager": f"{longhorn['manager']['repository']}:{longhorn['manager']['tag']}"
        }

        # Verify kubevirt version
        code, pods = api_client.get_pods(namespace=DEFAULT_HARVESTER_NAMESPACE)
        assert code == 200 and len(pods['data']) > 0, (
            f"Failed to get pods in namespace {DEFAULT_HARVESTER_NAMESPACE}")

        for pod in pods['data']:
            if "virt-operator" in pod['metadata']['name']:
                kubevirt_version_existed = (
                    kubevirt_operator_image == pod['spec']['containers'][0]['image'])

        # Verify longhorn version
        code, pods = api_client.get_pods(namespace=DEFAULT_LONGHORN_NAMESPACE)
        assert code == 200 and len(pods['data']) > 0, (
            f"Failed to get pods in namespace {DEFAULT_LONGHORN_NAMESPACE}")

        for pod in pods['data']:
            if "longhorn-manager" in pod['metadata']['name']:
                longhorn_manager_version_existed = (
                  longhorn_images["longhorn-manager"] == pod['spec']['containers'][0]['image'])
            elif "engine-image" in pod['metadata']['name']:
                engine_image_version_existed = (
                    longhorn_images["engine-image"] == pod['spec']['containers'][0]['image'])

        assert kubevirt_version_existed, "kubevirt version is not correct"
        assert engine_image_version_existed, "longhorn engine image version is not correct"
        assert longhorn_manager_version_existed, "longhorn manager version is not correct"

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_verify_crds_existed(self, api_client, harvester_crds):
        """ Verify crds existed
        Criteria:
        - crds should be existed
        """
        not_existed_crds = []
        exist_crds = True
        for crd in harvester_crds:
            code, _ = api_client.get_crds(name=crd)

            if code != 200:
                exist_crds = False
                not_existed_crds.append(crd)

        if not exist_crds:
            raise AssertionError(f"CRDs {not_existed_crds} are not existed")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_upgrade_vm_deleted(self, api_client, wait_timeout):
        # max to wait 300s for the upgrade related VMs to be deleted
        endtime = datetime.now() + timedelta(seconds=min(wait_timeout / 5, 300))
        while endtime > datetime.now():
            code, data = api_client.vms.get(namespace='harvester-system')
            upgrade_vms = [vm for vm in data['data'] if 'upgrade' in vm['id']]
            if not upgrade_vms:
                break
        else:
            raise AssertionError(f"Upgrade related VM still available:\n{upgrade_vms}")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_upgrade_volume_deleted(self, api_client, wait_timeout):
        # max to wait 300s for the upgrade related volumes to be deleted
        endtime = datetime.now() + timedelta(seconds=min(wait_timeout / 5, 300))
        while endtime > datetime.now():
            code, data = api_client.volumes.get(namespace='harvester-system')
            upgrade_vols = [vol for vol in data['data']
                            if 'upgrade' in vol['id'] and not vol['id'].endswith('log-archive')]
            if not upgrade_vols:
                break
        else:
            raise AssertionError(f"Upgrade related volume(s) still available:\n{upgrade_vols}")

    @pytest.mark.dependency(depends=["any_nodes_upgrade"])
    def test_upgrade_image_deleted(self, api_client, wait_timeout):
        # max to wait 300s for the upgrade related volumes to be deleted
        endtime = datetime.now() + timedelta(seconds=min(wait_timeout / 5, 300))
        while endtime > datetime.now():
            code, data = api_client.images.get(namespace='harvester-system')
            upgrade_images = [image for image in data['items']
                              if 'upgrade' in image['spec']['displayName']]
            if not upgrade_images:
                break
        else:
            raise AssertionError(f"Upgrade related image(s) still available:\n{upgrade_images}")
