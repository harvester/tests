import json
from time import sleep
from operator import add
from functools import reduce
from ipaddress import ip_address, ip_network
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.networks"
]


@pytest.fixture(scope='module')
def cluster_network(request, api_client, unique_name):
    vlan_nic = request.config.getoption('--vlan-nic')
    assert vlan_nic, f"VLAN NIC {vlan_nic} not configured correctly."

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


@pytest.mark.p0
@pytest.mark.settings
@pytest.mark.networks
@pytest.mark.skip_version_before('v1.0.3')
def test_storage_network(api_client, cluster_network, vlan_id, unique_name, wait_timeout):
    '''
    To cover test:
    - https://harvester.github.io/tests/manual/_incoming/1055_dedicated_storage_network/

    Prerequisites:
        - All VMs should be halted
        - All nodes should be selected in cluster network
    Steps:
        1. Create VM Network with the VLAN ID to get CIDR
        2. Delete the VM Network
        3. Create Storage Network with the cluster network, VLAN ID and IP Range(CIDR)
        4. Verify Storage Network be configured
    Expected Result:
        - Status of Storage Network should be `reason: Completed` and `status:True`
        - Pods of Longhorn's instance manager should be `status.phase: Running`
        - And should have value `metadata.annotations: k8s.v1.cni.cncf.io/network-status`
        - And one of the value should contains `interface:lhnet1`
            - And the value of `ips` should be in the IP Range
    '''
    # Prerequisite: VMs should be shutting down
    code, data = api_client.vms.get_status()
    assert 200 == code, (code, data)
    assert not data['data'], (
        "\n".join(
            f"VM({d['id']}) still in phase: {d['status']['phase']}"
            for d in data['data']
        )
    )

    # Get CIDR from VM Network
    code, data = api_client.networks.create(unique_name, vlan_id, cluster_network=cluster_network)
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
    _ = api_client.networks.delete(unique_name)
    cidr = route['cidr']

    # Create storage-network
    code, data = api_client.settings.get('storage-network')
    assert 200 == code, (code, data)
    origin_spec = api_client.settings.Spec.from_dict(data)
    spec = api_client.settings.StorageNetworkSpec.enable_with(
        vlan_id, cluster_network, cidr
    )
    code, data = api_client.settings.update('storage-network', spec)
    assert 200 == code, (code, data)

    # Verify Configuration is Completed
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.settings.get('storage-network')
        conds = data.get('status', {}).get('conditions', [])
        if conds and 'True' == conds[-1].get('status') and 'Completed' == conds[-1].get('reason'):
            break
        sleep(3)
    else:
        raise AssertionError(
            "Storage network updated but not completed.\n"
            f"API Status({code}): {data}"
        )

    # Verify Longhorn status
    done, ip_range = [], ip_network(cidr)
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.get_pods(namespace='longhorn-system')
        lh_instance_mgrs = [d for d in data['data']
                            if 'instance-manager' in d['id'] and d['id'] not in done]
        retries = []
        for im in lh_instance_mgrs:
            if 'Running' != im['status']['phase']:
                retries.append(im)
                continue
            nets = json.loads(im['metadata']['annotations']['k8s.v1.cni.cncf.io/network-status'])
            try:
                dedicated = next(n for n in nets if 'lhnet1' == n.get('interface'))
            except StopIteration:
                retries.append(im)
                continue

            if not all(ip_address(ip) in ip_range for ip in dedicated.get('ips', ['::1'])):
                retries.append(im)
                continue

        if not retries:
            break
        sleep(3)
    else:
        raise AssertionError(
            f"{len(retries)} Longhorn's instance manager not be updated after {wait_timeout}s\n"
            f"Not completed: {retries}"
        )

    # Teardown
    code, data = api_client.settings.update('storage-network', origin_spec)
    assert 200 == code, (code, data)
