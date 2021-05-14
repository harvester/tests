import pytest
import urllib.parse
import urllib3
import yaml
from time import sleep

urllib3.disable_warnings()

new_volume_data = {
                    "apiVersion": "cdi.kubevirt.io/v1beta1",
                    "kind": "DataVolume",
                    "metadata": {
                      "name": "test-volume",
                      "namespace": "default",
                      "labels": { "test.harvesterci.io": "for-test" },
                      "annotations": { "test.harvesterhci.io": "for-test" }
                    },
                    "spec": {
                      "source": {
                        "blank": {}
                      },
                      "pvc": {
                        "accessModes": ["ReadWriteMany"],
                        "volumeMode": "Block",
                        "storageClassName": "longhorn",
                        "resources": {
                          "requests":
                          {
                          }
                        }
                      }
                    }
                  }
@pytest.fixture(scope="class")
def volume_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/cdi.kubevirt.io.datavolumes')

def test_create_volume_missing_size(harvester_auth_session, volume_api_endpoint):
    resp = harvester_auth_session.post(volume_api_endpoint, json=new_volume_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == 'admission webhook \"datavolume-validate.cdi.kubevirt.io\" denied the request:  PVC size is missing'

def test_create_volume_missing_name(harvester_auth_session, volume_api_endpoint):
    new_volume_data["spec"]["pvc"]["resources"]["requests"]["storage"] = "1Gi"
    new_volume_data["metadata"]["name"] = ""
    resp = harvester_auth_session.post(volume_api_endpoint, json=new_volume_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == 'DataVolume.cdi.kubevirt.io \"\" is invalid: metadata.name: Required value: name or generateName is required'

def test_create_volumes(harvester_auth_session, volume_api_endpoint):
    new_volume_data["metadata"]["name"] = "test-volume"
    resp = harvester_auth_session.post(volume_api_endpoint, json=new_volume_data)
    volume_data = resp.json()
    assert resp.status_code == 201
    assert validate_blank_volumes(harvester_auth_session, volume_data['links']['view'])
    resp = harvester_auth_session.delete(volume_data['links']['remove'])
    assert resp.status_code == 204

def test_create_volume_by_yaml(harvester_auth_session, volume_api_endpoint):
    new_volume_data["metadata"]["name"] = "test-volume"
    resp = harvester_auth_session.post(volume_api_endpoint, data=yaml.dump(new_volume_data, sort_keys=False), headers={'Content-Type': 'application/yaml'})
    volume_data = resp.json()
    assert resp.status_code == 201
    assert validate_blank_volumes(harvester_auth_session, volume_data['links']['view'])
    resp = harvester_auth_session.delete(volume_data['links']['remove'])
    assert resp.status_code == 204    

def validate_blank_volumes(harvester_auth_session, get_api_link):
    for x in range(15):
       resp = harvester_auth_session.get(get_api_link)
       assert resp.status_code == 200
       ret_data = resp.json()
       sleep(5)
       if 'status' in ret_data and ret_data["status"]["phase"] == "Succeeded":
          assert ret_data["spec"] == new_volume_data["spec"]
          assert ret_data["metadata"]["labels"] == new_volume_data["metadata"]["labels"]
          assert ret_data["metadata"]["annotations"] == new_volume_data["metadata"]["annotations"]
          assert ret_data["status"]["phase"] == "Succeeded"
          return True
    return False

