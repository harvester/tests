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
from scenarios import utils
import pytest


pytest_plugins = [
   'scenarios.fixtures.api_endpoints',
   'scenarios.fixtures.api_version',
   'scenarios.fixtures.session',
  ]


def _generate_ssh_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend(),
    )

    private_key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption()
    )

    public_key = private_key.public_key()
    public_key_ssh = public_key.public_bytes(
        Encoding.OpenSSH,
        PublicFormat.OpenSSH
    )

    return public_key_ssh.decode('utf-8'), private_key_pem.decode('utf-8')


@pytest.fixture(scope='class')
def keypair(request, harvester_api_version, admin_session,
            harvester_api_endpoints):
    public_key, private_key = _generate_ssh_keypair()
    request_json = utils.get_json_object_from_template('basic_keypair',
        public_key=public_key
    )
    print('---%s---' % (harvester_api_endpoints.create_keypair))
    resp = admin_session.post(harvester_api_endpoints.create_keypair,
                              json=request_json)
    assert resp.status_code == 201, 'Unable to create keypair'
    keypair_data = resp.json()
    # NOTE(gyee): inject the private key to the keypair data so tests
    # have access to it, just in case they want to also test SSH into
    # the VM. This is not a security concern as this is for test only.
    keypair_data['spec']['privateKey'] = private_key
    yield keypair_data
    if not request.config.getoption('--do-not-cleanup'):
        resp = admin_session.delete(
            harvester_api_endpoints.delete_keypair % (
                keypair_data['metadata']['name']))
        assert resp.status_code == 200, 'Unable to cleanup keypair'
