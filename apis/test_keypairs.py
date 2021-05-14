import pytest
import urllib.parse
import urllib3
import sshpubkeys
import yaml
from Crypto.PublicKey import RSA
from time import sleep

urllib3.disable_warnings()

new_keypair_data = {
                    "apiVersion": "harvesterhci.io/v1beta1",
                    "kind": "KeyPair",
                    "metadata": {
                      "namespace": "default",  
                      "name": "test-key"
                    },
                    "spec": {
                      "publicKey": ""  
                    }  
                   }

@pytest.fixture(scope="class")
def keypair_api_endpoint(harvester_endpoint):
    return urllib.parse.urljoin(
        harvester_endpoint, '/v1/harvesterhci.io.keypair')

def generated_public_key():
    key = RSA.generate(1024)
    pubkey = key.publickey()
    pk = (pubkey.exportKey('OpenSSH')).decode("utf-8")
    return pk

def test_create_keypair_missing_name(harvester_auth_session, keypair_api_endpoint):
    pubkey = generated_public_key()
    new_keypair_data["metadata"]["name"] = "" 
    new_keypair_data["spec"]["publicKey"] = pubkey
    resp = harvester_auth_session.post(keypair_api_endpoint, json=new_keypair_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == 'KeyPair.harvesterhci.io \"\" is invalid: metadata.name: Required value: name or generateName is required'

def test_create_keypair_missing_key(harvester_auth_session, keypair_api_endpoint):
    new_keypair_data["spec"]["publicKey"] = ""
    new_keypair_data["metadata"]["name"] = "test-key"
    resp = harvester_auth_session.post(keypair_api_endpoint, json=new_keypair_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == "public key is required" 

def test_create_keypair_invalid_key(harvester_auth_session, keypair_api_endpoint):
    new_keypair_data["spec"]["publicKey"] = "invalid test public key"
    new_keypair_data["metadata"]["name"] = "test-key"
    resp = harvester_auth_session.post(keypair_api_endpoint, json=new_keypair_data)
    assert resp.status_code == 422
    response_data = resp.json()
    assert response_data["message"].strip() == "key is not in valid OpenSSH public key format"

#@pytest.mark.skip(reason='api unstable')
def test_create_keypairs(harvester_auth_session, keypair_api_endpoint):
    pubkey = generated_public_key()
    expectedFingerPrint = sshpubkeys.SSHKey(pubkey).hash_md5()
    new_keypair_data["metadata"]["name"] = "test-key"
    new_keypair_data["spec"]["publicKey"] = pubkey 
    resp = harvester_auth_session.post(keypair_api_endpoint, json=new_keypair_data)
    keypair_data = resp.json()
    assert resp.status_code == 201
    assert validate_fingerprint(harvester_auth_session, keypair_data['links']['view'], expectedFingerPrint)
    resp = harvester_auth_session.delete(keypair_data['links']['remove'])
    assert resp.status_code == 204

#@pytest.mark.skip(reason='api unstable')
def test_create_keypair_by_yaml(harvester_auth_session, keypair_api_endpoint):
    pubkey = generated_public_key()
    expectedFingerPrint = sshpubkeys.SSHKey(pubkey).hash_md5()
    new_keypair_data["metadata"]["name"] = "test-key"
    new_keypair_data["spec"]["publicKey"] = pubkey
    resp = harvester_auth_session.post(keypair_api_endpoint, data=yaml.dump(new_keypair_data, sort_keys=False), headers={'Content-Type': 'application/yaml'})
    keypair_data = resp.json()
    assert resp.status_code == 201
    assert validate_fingerprint(harvester_auth_session, keypair_data['links']['view'], expectedFingerPrint)
    resp = harvester_auth_session.delete(keypair_data['links']['remove'])
    assert resp.status_code == 204    

def validate_fingerprint(harvester_auth_session, get_api_link, fingerprint):
    for x in range(10):
       resp = harvester_auth_session.get(get_api_link)
       assert resp.status_code == 200
       ret_data = resp.json()
       sleep(2)
       if 'status' in ret_data:
          assert ret_data["spec"]["publicKey"] == new_keypair_data["spec"]["publicKey"]
          assert ("MD5:" + ret_data["status"]["fingerPrint"]) == fingerprint
          assert ret_data["status"]["conditions"][0]["type"] == "validated" 
          return True
    return False    
