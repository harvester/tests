import pytest
import urllib.parse
import yaml
import polling2

@pytest.fixture(scope="class")
def host_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/nodes')

def test_get_host(harvester_auth_session, harvester_cluster_nodes, host_api_endpoint):
    resp = harvester_auth_session.get(host_api_endpoint)
    host_data = resp.json() 
    assert resp.status_code == 200
    if harvester_cluster_nodes is None:
        with open('config.yml') as f:
             config_data = yaml.safe_load(f)
             harvester_cluster_nodes = config_data['harvester_cluster_nodes']

    assert len(host_data['data']) == harvester_cluster_nodes 

def test_verify_host_maintenance_mode(harvester_auth_session, host_api_endpoint):
    resp = harvester_auth_session.get(host_api_endpoint)
    assert resp.status_code == 200
    host_data = resp.json()
    nodeName = host_data['data'][0]['id']
    resp = harvester_auth_session.post(host_data['data'][0]['actions']['enableMaintenanceMode'])
    assert resp.status_code == 204        
    
    polling2.poll(
        lambda: harvester_auth_session.get(host_data['data'][0]['links']['view']).status_code == 200,
        step=5,
        poll_forever=True)
   
    resp = harvester_auth_session.get(host_data['data'][0]['links']['view'])
    resp.status_code == 200
    ret_data = resp.json()
    assert ret_data["spec"]["unschedulable"] == True 
    assert ret_data["metadata"]["annotations"]["harvesterhci.io/maintain-status"] in ["running", "completed"]

    resp = harvester_auth_session.get(host_api_endpoint)
    ret_data = resp.json()
    resp = harvester_auth_session.post(ret_data['data'][0]['actions']['disableMaintenanceMode'])
    assert resp.status_code == 204

    resp = harvester_auth_session.get(host_data['data'][0]['links']['view'])
    resp.status_code == 200
    ret_data = resp.json()
    assert "unschedulable" not in ret_data["spec"] 
    assert "harvesterhci.io/maintain-status" not in ret_data["metadata"]["annotations"]
