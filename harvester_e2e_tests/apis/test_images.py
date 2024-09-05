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
from pytest_cases import parametrize_with_cases, case

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
    "harvester_e2e_tests.fixtures.images",

]


class CasesImages:
    @case(tags='unique-name')
    def case_unique_name_long(self, unique_name):
        """basic unique_name_long

        Args:
            unique_name (_type_): fixture

        Returns:
            _type_: default setup with unique_name long
        """
        return (unique_name*6)[:43]

    @case(tags='unique-name')
    def case_unique_name_regular(self, unique_name):
        """basic unique_name_regular

        Args:
            unique_name (_type_): fixture

        Returns:
            _type_: default setup with unique_name regular
        """
        return unique_name

    @case(tags='gen-unique-name')
    def case_gen_unique_name_regular(self, gen_unique_name):
        """generate unique name regular

        Args:
            gen_unique_name (_type_): regular returns default fixture

        Returns:
            _type_: default setup with gen_unique_name lambda
        """
        return gen_unique_name

    @case(tags='gen-unique-name')
    def case_gen_unique_name_long(self, gen_unique_name):
        """generate unique name, but long version

        Args:
            gen_unique_name (_type_): long gen_unique_name is returned

        Returns:
            _type_: long gen_unique_name on demand but long
        """
        current = datetime.now().strftime("%Hh%Mm%Ss%f-%m-%d")
        current_long = (current*6)[:43]
        return lambda: current_long


@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.images
class TestImagesNegative:
    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_get_not_exist(self, api_client, unique_name):
        code, data = api_client.images.get(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get('reason'), (code, data)

    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_delete_not_exist(self, api_client, unique_name):
        code, data = api_client.images.delete(unique_name)

        assert 404 == code, (code, data)
        assert "NotFound" == data.get("reason"), (code, data)

    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_create_with_empty_data(self, api_client, unique_name):
        # name, url, description, sourcetype, namespace
        image_json = api_client.images.create_data(unique_name, "", "", "", "")
        code, data = api_client.images.create(unique_name, json=image_json)

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("reason"), (code, data)

    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_create_with_empty_url(self, api_client, unique_name):
        code, data = api_client.images.create_by_url(unique_name, "")

        assert 422 == code, (code, data)
        assert "Invalid" == data.get("reason"), (code, data)


@pytest.mark.p0
@pytest.mark.images
class TestImages:

    @pytest.mark.dependency(name="create_image")
    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_create(self, api_client, unique_name, fake_image_file):
        resp = api_client.images.create_by_file(unique_name, fake_image_file)

        assert 200 == resp.status_code, (
            f"Failed to upload fake image with error:{resp.status_code}, {resp.content}"
        )

    @pytest.mark.dependency(name="get_image")
    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_get(self, api_client, unique_name):
        # Case 1: get all images
        code, data = api_client.images.get()

        assert len(data['items']) > 0, (code, data)

        # Case 2: get created image
        code, data = api_client.images.get(unique_name)
        assert 200 == code, (code, data)
        assert unique_name == data['metadata']['name']

    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_update(self, api_client, unique_name):
        updates = {
            "labels": {
                "test-label": "42"
            },
            "annotations": {
                "test-annotation": "dummy",
                "field.cattle.io/description": 'test description'
            },

        }

        code, data = api_client.images.update(unique_name, dict(metadata=updates))

        assert 200 == code, (f"Failed to update image with error: {code}, {data}")

        unexpected = list()
        for field, pairs in updates.items():
            for k, val in pairs.items():
                if data['metadata'][field].get(k) != val:
                    unexpected.append((field, k, val, data['metadata'][field].get(k)))

        assert not unexpected, (
            "\n".join(f"Update {f} failed, set key {k} as {v} but got {n}"
                      for f, k, v, n in unexpected)
        )

    @pytest.mark.dependency(name="delete_image")
    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_delete(self, api_client, unique_name, wait_timeout):
        code, data = api_client.images.delete(unique_name)

        assert 200 == code, (f"Failed to delete image with error: {code}, {data}")

        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete image {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )

    @pytest.mark.skip_version_if("> v1.2.0", "<= v1.4.0", reason="Issue#4293 fix after `v1.4.0`")
    @pytest.mark.dependency(depends=["create_image", "get_image", "delete_image"])
    @parametrize_with_cases("unique_name", cases=CasesImages, has_tag='unique-name')
    def test_create_with_reuse_display_name(
            self, wait_timeout, api_client, unique_name, fake_image_file):
        code, data = api_client.images.get(unique_name)

        assert 404 == code, f"Image {unique_name} not be deleted by previous test."

        resp = api_client.images.create_by_file(unique_name, fake_image_file)

        assert 200 == resp.status_code, (
            f"failed to upload fake image with reused name {unique_name}, "
            f"got error: {resp.status_code}, {resp.content}"
        )

        _ = api_client.images.delete(unique_name)
        endtime = datetime.now() + timedelta(seconds=wait_timeout)

        while endtime > datetime.now():
            code, data = api_client.images.get(unique_name)
            if code == 404:
                break
            sleep(5)
        else:
            raise AssertionError(
                f"Failed to delete image {unique_name} with {wait_timeout} timed out\n"
                f"Still got {code} with {data}"
            )


@pytest.mark.dependency(depends=["create_image", "get_image", "delete_image"])
@pytest.mark.p0
@pytest.mark.negative
@pytest.mark.images
@parametrize_with_cases("gen_unique_name", cases=CasesImages, has_tag='gen-unique-name')
def test_create_with_invalid_url(api_client, gen_unique_name, wait_timeout):
    unique_name = gen_unique_name()
    code, data = api_client.images.create_by_url(unique_name, f"https://{unique_name}.img")

    assert 201 == code, (code, data)

    endtime = datetime.now() + timedelta(seconds=wait_timeout)
    while endtime > datetime.now():
        code, data = api_client.images.get(unique_name)
        image_conds = data.get('status', {}).get('conditions', [])
        if len(image_conds) > 0 and "Initialized" == image_conds[-1].get("type"):
            break
        sleep(3)

    assert len(image_conds) in (1, 2), f"Got unexpected image conditions!\n{data}"
    assert "Initialized" == image_conds[-1].get("type")
    assert "False" == image_conds[-1].get("status")
    assert "no such host" in image_conds[-1].get("message")

    api_client.images.delete(unique_name)
