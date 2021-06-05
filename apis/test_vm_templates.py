import pytest
import urllib.parse
import urllib3
import yaml
import json
import os
from time import sleep

urllib3.disable_warnings()

new_template_data = {
                    "apiVersion": "harvesterhci.io/v1beta1",
                    "kind": "VirtualMachineTemplate",
                    "metadata": {
                      "name": "test-raw-image-base-template",
                      "namespace": "harvester-system",
                      "labels": { "test.harvesterci.io": "test-raw-image-base-template" }
                    },
                    "spec": {
                      "description": "Test Raw Image Base Template"
                    }
                  }

@pytest.fixture(scope="class")
def template_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.virtualmachinetemplates')

@pytest.fixture(scope="class")    
def template_version_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.virtualmachinetemplateversion')
    
def test_verify_default_vm_templates(harvester_auth_session, template_api_endpoint):
    resp = harvester_auth_session.get(template_api_endpoint)
    assert resp.status_code == 200
    ret_user_data = resp.json()
    assert len(ret_user_data['data']) == 3 

def test_verify_default_vm_template_versions(harvester_auth_session, template_version_api_endpoint):
    resp = harvester_auth_session.get(template_version_api_endpoint)
    assert resp.status_code == 200
    ret_user_data = resp.json()
    assert len(ret_user_data['data']) == 3 

def test_create_verify_vm_template(harvester_auth_session, template_api_endpoint, template_version_api_endpoint):
    resp = harvester_auth_session.post(template_api_endpoint, json=new_template_data)
    template_data = resp.json()
    assert resp.status_code == 201

    resp = harvester_auth_session.post(template_version_api_endpoint, json=get_json_data("templateVersion.json"))
    template_version_data = resp.json()
    assert resp.status_code == 201

    assert validate_vm_template_version(harvester_auth_session, template_data['links']['view'])

    resp = harvester_auth_session.delete(template_version_data['links']['remove'])
    assert resp.status_code == 500 

    resp = harvester_auth_session.delete(template_data['links']['remove'])
    assert resp.status_code == 204

def get_json_data(json_data_filename):
    data_dir = os.getcwd() + "/apis/data"
    json_data_file = os.path.join(data_dir, json_data_filename)
    with open(json_data_file) as f:
       new_json_data = json.load(f)
    return new_json_data

def validate_vm_template_version(harvester_auth_session, get_api_link):
    for x in range(10):
       resp = harvester_auth_session.get(get_api_link)
       assert resp.status_code == 200
       ret_data = resp.json()
       sleep(5)
       if 'status' in ret_data:
          assert ret_data["spec"]["defaultVersionId"] == "harvester-system/test-raw-image-base-version" 
          assert ret_data["status"]["defaultVersion"] == 1 
          assert ret_data["status"]["latestVersion"] == 1 
          return True
    return False


