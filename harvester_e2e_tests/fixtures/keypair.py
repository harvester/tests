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

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    NoEncryption,
    Encoding,
    PrivateFormat,
    PublicFormat)
from harvester_e2e_tests import utils
import pytest
import time


pytest_plugins = [
   'harvester_e2e_tests.fixtures.api_endpoints',
   'harvester_e2e_tests.fixtures.api_version',
   'harvester_e2e_tests.fixtures.session',
  ]


def _generate_ssh_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend(),
    )

    private_key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.OpenSSH,
        NoEncryption()
    )

    public_key = private_key.public_key()
    public_key_ssh = public_key.public_bytes(
        Encoding.OpenSSH,
        PublicFormat.OpenSSH
    )

    return public_key_ssh.decode('utf-8'), private_key_pem.decode('utf-8')


def wait_till_validated(admin_session, harvester_api_endpoints, keypair_data):
    for x in range(10):
        resp = admin_session.get(harvester_api_endpoints.get_keypair % (
            keypair_data['metadata']['name']))
        assert resp.status_code == 200, (
            'Unable to get keypair: %s' % (resp.content))
        resp_json = resp.json()
        if ('status' in resp_json and
                resp_json['status']['conditions'][0]['type'] == 'validated'):
            return
        time.sleep(10)
    pytest.fail('Timed out while waiting for keypair to be validated')


@pytest.fixture(scope='class')
def keypair_request_json():
    public_key, private_key = _generate_ssh_keypair()
    request_json = utils.get_json_object_from_template(
        'basic_keypair',
        public_key=public_key
    )
    return [request_json, private_key]


@pytest.fixture(scope='class')
def keypair(request, harvester_api_version, admin_session,
            harvester_api_endpoints, keypair_request_json):
    resp = admin_session.post(harvester_api_endpoints.create_keypair,
                              json=keypair_request_json[0])
    assert resp.status_code == 201, 'Unable to create keypair'
    keypair_data = resp.json()
    assert keypair_data['spec']['publicKey'] == \
        keypair_request_json[0]['spec']['publicKey'], (
            'Created publicKey does not match original publicKey')
    wait_till_validated(admin_session, harvester_api_endpoints, keypair_data)
    # NOTE(gyee): inject the private key to the keypair data so tests
    # have access to it, just in case they want to also test SSH into
    # the VM. This is not a security concern as this is for test only.
    keypair_data['spec']['privateKey'] = keypair_request_json[1]
    yield keypair_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_keypair % (
                keypair_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup keypair'
