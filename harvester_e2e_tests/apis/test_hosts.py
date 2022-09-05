# Copyright (c) 2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

from time import sleep
from datetime import datetime, timedelta

import yaml
import pytest

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client"
]


@pytest.mark.dependency(name="get_host")
@pytest.mark.hosts
@pytest.mark.p1
def test_get_host(api_client):
    # Case 1: Get all nodes
    status_code, nodes_info = api_client.hosts.get()

    assert status_code == 200, f"Failed to list nodes with error: {nodes_info}"
    assert len(nodes_info['data']) >= 1, "Incorrect hosts amount"

    # Case 2: Get specific node
    node_id = nodes_info['data'][-1]['id']

    status_code, node = api_client.hosts.get(node_id)

    assert status_code == 200, f"Failed ot get node {node_id} with error: {node}"
    assert node_id == node['id'], f"Responsed unexpected Node {node['id']}"


@pytest.mark.dependency(depends=["get_host"], name="enable_maintenance_mode")
@pytest.mark.hosts
@pytest.mark.p2
def test_maintenance_mode(api_client):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-03-Verify Enabling maintenance mode
        hosts-12-Host with no VMs on it
    """

    _, nodes_info = api_client.hosts.get()

    # Test on the last node to avoid affect VIP
    node = nodes_info['data'][-1]

    # Case 1: enable
    status_code, node_stats = api_client.hosts.maintenance_mode(node['id'], enable=True)
    maintain_status = node_stats["metadata"]["annotations"]["harvesterhci.io/maintain-status"]

    assert node_stats["spec"]["unschedulable"]
    assert maintain_status in ("running", "completed")

    # Case 2: disable
    status_code, node_stats = api_client.hosts.maintenance_mode(node['id'], enable=False)

    assert "unschedulable" not in node_stats["spec"]
    assert "harvesterhci.io/maintain-status" not in node_stats["metadata"]["annotations"]


@pytest.mark.dependency(depends=["get_host"])
@pytest.mark.hosts
@pytest.mark.p1
def test_update_node(api_client):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-04-Edit Config Add description and other details
    """

    fields = ('field.cattle.io/description', 'harvesterhci.io/host-custom-name')

    _, nodes_info = api_client.hosts.get()

    # There is no different to update any nodes, so we use the last.
    node = nodes_info['data'][-1]
    original_annotations = {k: node['metadata']['annotations'].get(k, "")
                            for k in fields}

    test_annotations = {k: f"Test_update_{k}_{datetime.now()}" for k in fields}
    test_data = dict(metadata=dict(annotations=test_annotations))

    status_code, node_stats = api_client.hosts.update(node['id'], test_data)

    not_updated_fields = list()
    for k, v in test_annotations.items():
        if node_stats['metadata']['annotations'].get(k) != v:
            not_updated_fields.append((k, v, node_stats['metadata']['annotations'].get(k)))

    assert len(not_updated_fields) == 0, (
        f"Fields not fully updated, API return `{status_code}`\n"
        "\n".join(f"field:{k}, expected: {v}, got {o}" for k, v, o in not_updated_fields)
    )

    # For teardown
    _ = api_client.hosts.update(node['id'],
                                dict(metadata=dict(annotations=original_annotations)))


@pytest.mark.dependency(depends=["get_host"])
@pytest.mark.hosts
@pytest.mark.p1
def test_update_using_yaml(api_client):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-05-Edit through Yaml
    """

    fields = ('field.cattle.io/description', 'harvesterhci.io/host-custom-name')

    _, nodes_info = api_client.hosts.get()

    # There is no different to update any nodes, so we use the last.
    node = nodes_info['data'][-1]
    original_annotations = {k: node['metadata']['annotations'].get(k, "")
                            for k in fields}

    test_annotations = {k: f"Test_update_{k}_{datetime.now()}" for k in fields}
    for k, v in test_annotations.items():
        node['metadata']['annotations'][k] = v

    api_client.hosts.update(node['id'], yaml.dump(node, sort_keys=False), as_json=False,
                            headers={"Content-Type": "application/yaml"})

    status_code, node_stats = api_client.hosts.get(node['id'])

    not_updated_fields = list()
    for k, v in test_annotations.items():
        if node_stats['metadata']['annotations'].get(k) != v:
            not_updated_fields.append((k, v, node_stats['metadata']['annotations'].get(k)))

    assert len(not_updated_fields) == 0, (
        f"Fields not fully updated, API return `{status_code}`\n"
        "\n".join(f"field:{k}, expected: {v}, got {o}" for k, v, o in not_updated_fields)
    )

    # For teardown
    _ = api_client.hosts.update(node['id'],
                                dict(metadata=dict(annotations=original_annotations)))


@pytest.mark.dependency(depends=["get_host"], name="delete_host")
@pytest.mark.p1
@pytest.mark.hosts
@pytest.mark.delete_host
def test_delete_host(api_client, wait_timeout):
    """
    Test the hosts are the nodes which make the cluster
    Covers:
        hosts-07-Delete the host
    """
    _, nodes_info = api_client.hosts.get()

    node = nodes_info['data'][-1]

    delete_resp = api_client.hosts.delete(node['id'])

    endtime = datetime.now() + timedelta(seconds=wait_timeout)

    while endtime > datetime.now():
        status_code, node_stats = api_client.hosts.get(node['id'])
        if status_code == 404:
            break
        sleep(5)
    else:
        raise AssertionError(f"Failed to delete host {node['id']}\n",
                             f"Delete response: {delete_resp}\n"
                             f"timeout {wait_timeout} and still got: {status_code}, {node_stats}")
