import pytest
import urllib.parse
import urllib3
import bcrypt


urllib3.disable_warnings()

new_user_data = {'apiVersion': 'harvesterhci.io/v1beta1',
                 'kind': 'User',
                 'displayName': 'Foo Bar',
                 'description': 'Test create Foo Bar',
                 'username': 'foo',
                 'password': 'TestF00Bar101',
                 'isAdmin': False}

@pytest.fixture(scope="class")
def user_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.users')

def test_create_users(harvester_auth_session, user_api_endpoint):
    resp = harvester_auth_session.post(user_api_endpoint, json=new_user_data)
    user_data = resp.json()
    assert resp.status_code == 201
    assert user_data['displayName'] == 'Foo Bar'
    assert user_data['description'] == 'Test create Foo Bar'
    assert user_data['username'] == 'foo'
    # TODO(gyee): check output here
    # {'id': 'u-fqtli23i77', 'type': 'harvesterhci.io.user', 'links': {'remove': 'https://10.42.0.62:8443/v1/harvesterhci.io.users/u-fqtli23i77', 'self': 'https://10.42.0.62:8443/v1/harvesterhci.io.users/u-fqtli23i77', 'update': 'https://10.42.0.62:8443/v1/harvesterhci.io.users/u-fqtli23i77', 'view': 'https://10.42.0.62:8443/apis/harvesterhci.io/v1beta1/users/u-fqtli23i77'}, 'apiVersion': 'harvesterhci.io/v1beta1', 'description': 'Test create Foo Bar', 'displayName': 'Foo Bar', 'isAdmin': False, 'kind': 'User', 'metadata': {'creationTimestamp': '2021-04-28T06:25:20Z', 'fields': ['u-fqtli23i77', 'Foo Bar', 'foo', 'Test create Foo Bar'], 'generation': 1, 'managedFields': [{'apiVersion': 'harvesterhci.io/v1beta1', 'fieldsType': 'FieldsV1', 'fieldsV1': {'f:description': {}, 'f:displayName': {}, 'f:isAdmin': {}, 'f:password': {}, 'f:username': {}}, 'manager': 'harvester', 'operation': 'Update', 'time': '2021-04-28T06:25:20Z'}], 'name': 'u-fqtli23i77', 'relationships': None, 'resourceVersion': '267116', 'state': {'error': False, 'message': 'Resource is current', 'name': 'active', 'transitioning': False}, 'uid': 'a4f482aa-6127-4a2b-8fc8-dd8fe3533353'}, 'username': 'foo'}
    resp = harvester_auth_session.delete(user_data['links']['remove'])
    assert resp.status_code == 204

def test_list_user(harvester_auth_session, user_api_endpoint):
    resp = harvester_auth_session.post(user_api_endpoint, json=new_user_data)
    user_data = resp.json()
    assert resp.status_code == 201
    resp = harvester_auth_session.get(user_data['links']['view'])
    assert resp.status_code == 200
    ret_user_data = resp.json()
    assert ret_user_data['displayName'] == 'Foo Bar'
    assert ret_user_data['description'] == 'Test create Foo Bar'
    assert ret_user_data['username'] == 'foo'
    resp = harvester_auth_session.delete(user_data['links']['remove'])
    assert resp.status_code == 204

def test_update_user_password(harvester_auth_session, user_api_endpoint):
    resp = harvester_auth_session.post(user_api_endpoint, json=new_user_data)
    user_data = resp.json()
    assert resp.status_code == 201
    resourceVersion = user_data['metadata']['resourceVersion']
    name = user_data['metadata']['name']
    updated_user_data = {'apiVersion': 'harvesterhci.io/v1beta1',
                         'kind': 'User',
                         'displayName': 'Foo Bar',
                         'description': 'Test create Foo Bar',
                         'username': 'foo',
                         'password': 'TestF00Bar',
                         'isAdmin': False,
                         'metadata': {
                           'resourceVersion': "",
                           'name': ""
                         }      
                        }
    updated_user_data['metadata']['resourceVersion'] = resourceVersion
    updated_user_data['metadata']['name'] = name
    resp = harvester_auth_session.put(user_data['links']['update'], json=updated_user_data)
    assert resp.status_code == 200
    updated_user_data = resp.json()
    resp = harvester_auth_session.get(updated_user_data['links']['view'])
    assert resp.status_code == 200        
    get_updated_user = resp.json()        
    updatedPassStr = str.encode("TestF00Bar")
    hashedPass = bcrypt.hashpw(updatedPassStr, bcrypt.gensalt()) 
    assert bcrypt.checkpw(updatedPassStr, get_updated_user['password'].encode("utf-8")) == True  
    resp = harvester_auth_session.delete(user_data['links']['remove'])
    assert resp.status_code == 204
    

