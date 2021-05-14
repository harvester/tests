import pytest
import urllib.parse

new_settings_data = {
                      "apiVersion": "harvesterhci.io/v1beta1",
                      "kind": "Setting",
                      "metadata": {
                        "name": "api-ui-version",
                        "resourceVersion": ""
                      },
                      "value": "v0.0.0"
                     }

@pytest.fixture(scope="class")
def settings_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.settings')

@pytest.fixture(scope="class")
def settings_version_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.settings/api-ui-version')

def test_list_settingss(harvester_auth_session, settings_api_endpoint):
    resp = harvester_auth_session.get(settings_api_endpoint)
    assert resp.status_code == 200

def test_update_api_ui_version(harvester_auth_session, settings_version_api_endpoint):
    resp = harvester_auth_session.get(settings_version_api_endpoint)
    api_ui_version_data = resp.json()
    new_settings_data["metadata"]["resourceVersion"] = api_ui_version_data["metadata"]["resourceVersion"] 
    resp = harvester_auth_session.put(api_ui_version_data['links']['update'], json=new_settings_data)
    updated_settings_data = resp.json()
    assert resp.status_code == 200
    assert updated_settings_data['value'] == new_settings_data['value'] 
