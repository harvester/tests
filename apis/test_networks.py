import pytest
import urllib.parse
import urllib3
import yaml
import json
import os
import polling2
import uuid
from time import sleep

urllib3.disable_warnings()

config_data = '{{\"cniVersion\":\"0.3.1\",\"name\":\"test-network\",\"type\":\"bridge\",\"bridge\":\"harvester-br0\",\"promiscMode\":true,\"vlan\":{},\"ipam\":{{}}}}'

@pytest.fixture(scope="class")
def network_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/k8s.cni.cncf.io.network-attachment-definitions')

def test_create_with_vid_0(harvester_auth_session, network_api_endpoint):
    network_data = get_json_data("network.json")
    network_data["metadata"]["name"] = uuid.uuid4().hex
    network_data["spec"]["config"] = config_data.format(0, '')
    resp = harvester_auth_session.post(network_api_endpoint, json=network_data)
    assert resp.status_code == 422 
    response_data = resp.json()
    assert response_data["message"].strip() == "Bridge vlan vid must \u003e=1 and \u003c=4094"

def test_create_with_vid_4095(harvester_auth_session, network_api_endpoint):
    network_data = get_json_data("network.json")
    network_data["metadata"]["name"] = uuid.uuid4().hex
    network_data["spec"]["config"] = config_data.format(4095, '')
    resp = harvester_auth_session.post(network_api_endpoint, json=network_data)
    assert resp.status_code == 422 
    response_data = resp.json()
    assert response_data["message"].strip() == "Bridge vlan vid must \u003e=1 and \u003c=4094"

def test_create_edit_network(harvester_auth_session, network_api_endpoint):
    network_data = get_json_data("network.json")
    network_data["metadata"]["name"] = uuid.uuid4().hex
    resp = harvester_auth_session.post(network_api_endpoint, json=network_data)
    network_data = resp.json()
    assert resp.status_code == 201
    assert network_data["metadata"]["labels"] == { "networks.harvesterhci.io/type": "L2VlanNetwork" }
    
    polling2.poll(
        lambda: harvester_auth_session.get(network_data['links']['view']).status_code == 200,
        step=5,
        poll_forever=True)

    resp = harvester_auth_session.get(network_data['links']['view'])
    assert resp.status_code == 200
    net_data = resp.json()    
    net_data["spec"]["config"] = config_data.format(10, '') 
    resp = harvester_auth_session.put(network_data['links']['update'], json=net_data)
    assert resp.status_code == 200
    updated_network_data = resp.json()
    updated_config = json.loads(updated_network_data["spec"]["config"])
    assert updated_config["vlan"] == 10
    resp = harvester_auth_session.delete(network_data['links']['remove'])
    assert resp.status_code in [200,204] 

def get_json_data(json_data_filename):
    data_dir = os.getcwd() + "/apis/data"
    json_data_file = os.path.join(data_dir, json_data_filename)
    with open(json_data_file) as f:
       new_json_data = json.load(f)
    return new_json_data
