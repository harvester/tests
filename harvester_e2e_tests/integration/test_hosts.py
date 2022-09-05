from time import sleep
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.hosts
@pytest.mark.p1
@pytest.mark.host_management
def test_host_poweroff_state(api_client, host_state, wait_timeout):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-01-Negative test-Verify the state for Powered down node
    """
    _, nodes_info = api_client.hosts.get()

    node = nodes_info['data'][-1]
    node_ip = next(val["address"] for val in node['status']['addresses']
                   if val["type"] == "InternalIP")

    rc, out, err = host_state.power(node['id'], node_ip, on=False)
    assert rc == 0, (f"Failed to PowerOff node {node['id']} with error({rc}):\n"
                     f"stdout: {out}\n\nstderr: {err}")
    sleep(host_state.delay)  # Wait for the node to disappear
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        _, metric = api_client.hosts.get_metrics(node['id'])
        if metric.get("status") == 404:
            break
        sleep(5)
    else:
        raise AssertionError(f"Node {node['id']} still available after PowerOff script executed"
                             f", script path: {host_state.path}")

    _, node = api_client.hosts.get(node['id'])
    assert node["metadata"]["state"]["name"] in ("in-progress", "unavailable")


@pytest.mark.hosts
@pytest.mark.p1
@pytest.mark.host_management
def test_host_poweron_state(api_client, host_state, wait_timeout):
    _, nodes_info = api_client.hosts.get()

    node = nodes_info['data'][-1]
    node_ip = next(val["address"] for val in node['status']['addresses']
                   if val["type"] == "InternalIP")

    rc, out, err = host_state.power(node['id'], node_ip, on=True)
    assert rc == 0, (f"Failed to PowerOn node {node['id']} with error({rc}):\n"
                     f"stdout: {out}\n\nstderr: {err}")
    sleep(host_state.delay)  # Wait for the node to disappear
    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        _, metric = api_client.hosts.get_metrics(node['id'])
        if not metric.get("metadata", {}).get("state", {}).get("error"):
            break
        sleep(5)
    else:
        raise AssertionError(f"Node {node['id']} still unavailable after PowerOn script executed"
                             f", script path: {host_state.path}")

    _, node = api_client.hosts.get(node['id'])
    assert "active" == node["metadata"]["state"]["name"]
