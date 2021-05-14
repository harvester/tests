import pytest
import urllib.parse

new_image_data = {
                      "apiVersion": "harvesterhci.io/v1beta1",
                      "kind": "VirtualMachineImage",
                      "metadata": {
                        "name": "test-image",
                        "namespace": "default",
                        "labels": { "test.harvesterhci.io": "for-test" },
                        "annotations": { "test.harvesterhci.io": "for-test" },
                      },
                      "spec": {
                        "displayName": "Test Image Ubuntu",
                        "url": "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img"
                      }
                     }

@pytest.fixture(scope="class")
def image_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.virtualmachineimages')

def test_list_images(harvester_auth_session, image_api_endpoint):
    resp = harvester_auth_session.get(image_api_endpoint)
    assert resp.status_code == 200

def test_create_image_no_data(harvester_auth_session, image_api_endpoint):
    no_image_data = {
                      "apiVersion": "harvesterhci.io/v1beta1",
                      "kind": "VirtualMachineImage"
                     }  
    resp = harvester_auth_session.post(image_api_endpoint, json=no_image_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == "Name is required."

def test_create_image_no_url(harvester_auth_session, image_api_endpoint):
    new_image_data["spec"]["url"] = ""
    resp = harvester_auth_session.post(image_api_endpoint, json=new_image_data)
    image_data = resp.json()
    assert resp.status_code == 201 
    resp = harvester_auth_session.delete(image_data['links']['remove'])
    assert resp.status_code == 204

def test_create_images(harvester_auth_session, image_api_endpoint):
    new_image_data["spec"]["url"] = "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img"
    resp = harvester_auth_session.post(image_api_endpoint, json=new_image_data)
    image_data = resp.json()
    assert resp.status_code == 201
    assert image_data['metadata']['name'] == "test-image"
    resp = harvester_auth_session.delete(image_data['links']['remove'])
    assert resp.status_code == 204

def test_update_images(harvester_auth_session, image_api_endpoint):
    resp = harvester_auth_session.post(image_api_endpoint, json=new_image_data)
    image_data = resp.json()
    assert resp.status_code == 201
    assert image_data['metadata']['labels'] == { 'test.harvesterhci.io': 'for-test' }
    assert image_data['metadata']['annotations'] == { 'test.harvesterhci.io': 'for-test' }
    resourceVersion = image_data['metadata']['resourceVersion']
    new_image_data["metadata"]["labels"] = { "test.harvesterhci.io": "for-test-update" }
    new_image_data["metadata"]["annotations"] = { "test.harvesterhci.io": "for-test-update" }
    new_image_data['metadata']['resourceVersion'] = resourceVersion
    resp = harvester_auth_session.put(image_data['links']['update'], json=new_image_data)
    update_image_data = resp.json()
    assert resp.status_code == 200
    assert update_image_data["metadata"]["labels"] == { "test.harvesterhci.io": "for-test-update" }
    assert update_image_data["metadata"]["annotations"] == { "test.harvesterhci.io": "for-test-update" }
    resp = harvester_auth_session.delete(image_data['links']['remove'])
    assert resp.status_code == 204
