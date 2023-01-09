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

from time import sleep
from datetime import datetime, timedelta

import pytest

pytest_plugins = [
    'harvester_e2e_tests.fixtures.api_endpoints',
    'harvester_e2e_tests.fixtures.volume',
    'harvester_e2e_tests.fixtures.session',
    'harvester_e2e_tests.fixtures.image',
    'harvester_e2e_tests.fixtures.api_client'
]


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.volumes
class TestVolumesNegative:
    def test_get_not_exist(self, api_client, unique_name):
        """
        1. Tries to get a volume that doesn't exist
        2. Checks that the get command gets a 404
        """
        code, data = api_client.volumes.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('code'), (code, data)

    def test_delete_not_exist(self, api_client, unique_name):
        """
        1. Tries to delete a volume that doesn't exist
        2. Checks that it gets a 404
        """
        code, data = api_client.volumes.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get("code"), (code, data)

    def test_create_without_size(self, api_client, unique_name):
        """
        1. Tries to create a volume without a size
        2. Checks that it gets a 422
        """
        spec = api_client.volumes.Spec(0)
        code, data = api_client.volumes.create(unique_name, spec)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("code"), (code, data)

    def test_create_without_name(self, api_client):
        """
        1. Tries to create a volume without a name
        2. Checks that it gets a  422
        """
        spec = api_client.volumes.Spec(1)
        code, data = api_client.volumes.create("", spec)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("code"), (code, data)


@pytest.mark.p0
@pytest.mark.volumes
class TestVolumes:
    def test_create(self, api_client, unique_name):
        """
        1. Create a new image from the default entries in the spec
        2. Check that the create command gets a 201 response
        """
        spec = api_client.volumes.Spec(1)
        code, data = api_client.volumes.create(unique_name, spec)

        assert 201 == code, (code, data)

    def test_get(self, api_client, unique_name):
        """
        1. Runs a get command on the volume created in the previous test
        note: this will fail if you run it by itslef
        2. It will fail if it doesn't return a 200
        """
        # Case 1: get all volumes
        code, data = api_client.volumes.get()

        assert 200 == code, (code, data)
        assert len(data['data']) > 0, (code, data)

        # Case 2: get specific volume
        code, data = api_client.volumes.get(unique_name)

        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name'], (code, data)

    def test_update_size(self, api_client, unique_name, wait_timeout):
        """
        1. Updates the volume created in the previous test to 10GB
        note: this will fail if you run it by itslef
        2. It will loop while waiting for it to update and error out if it doesn't
        """
        # Pre-condition: Volume is Ready
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(unique_name)
            if "Bound" == data['status']['phase']:
                break
            sleep(5)
        else:
            raise AssertionError(
                "Volume not changed to phase: _Bound_ with {wait_timeout} timed out\n"
                f"Got error: {code}, {data}"
            )

        spec = api_client.volumes.Spec.from_dict(data)
        spec.size = "10Gi"
        code, data = api_client.volumes.update(unique_name, spec)

        assert 200 == code, (f"Failed to update volume with error: {code}, {data}")

    def test_delete(self, api_client, unique_name, wait_timeout):
        """
        1. Deletes the volume created in the previous test
        note: this will fail if you run it by itslef
        2. It will loop while waiting for it to delete and error out if it doesn't
        """
        code, data = api_client.volumes.delete(unique_name)

        assert 200 == code, (f"Failed to delete volume with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            code, data = api_client.volumes.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete volume {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    def test_create_volume_backing_image(self, request, api_client, unique_name):
        """
        1. Create a new image from URL
        2. Check that it is created succesffully.
        3. Create a new volume with the image_id of the previous image
        4. Check that the new image is created
        5. Delete image and volume if required
        """

        url = request.config.getoption('--opensuse-image-url')
        code, image_data = api_client.images.create_by_url(unique_name, url)
        if code != 201:
            raise AssertionError(
                f"Failed to create image {unique_name} from URL got\n"
                f"Creation got {code} with {image_data}"
            )

        assert 201 == code, (code, image_data)

        endtime = datetime.now() + timedelta(minutes=3)
        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            image_conds = data.get('status', {}).get('conditions', [])
            if len(image_conds) > 0:
                break
            sleep(3)

        assert "Initialized" == image_conds[len(image_conds)-1].get("type")
        assert "True" == image_conds[len(image_conds)-1].get("status")
        spec = api_client.volumes.Spec(1)
        spec.size = "10Gi"
        # spec.storage_cls = "longhorn-" + image_data["spec"]["displayName"]
        image_id_temp = image_data["metadata"]["namespace"] + '/' + image_data["metadata"]["name"]
        code, data = api_client.volumes.create(unique_name, spec, image_id=image_id_temp)

        # This is for checking that the volume was created
        code, volume_data = api_client.volumes.get(unique_name)
        assert 200 == code, (code, volume_data)
        assert unique_name == volume_data['metadata']['name'], (code, volume_data)
        assert image_id_temp == volume_data['id']

        if not request.config.getoption('--do-not-cleanup'):
            api_client.images.delete(unique_name)
            api_client.volumes.delete(unique_name)
