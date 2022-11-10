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
import warnings

import pytest

pytest_plugins = [
   "harvester_e2e_tests.fixtures.api_client"
  ]


@pytest.mark.p0
@pytest.mark.settings
def test_get_all_settings(api_client, expected_settings):
    expected_settings = expected_settings['default']
    code, data = api_client.settings.get()

    available_settings = {m['metadata']['name'] for m in data['items']}

    assert 200 == code, (code, data)
    assert expected_settings <= available_settings, (
        "Some setting missing:\n"
        f"{expected_settings - available_settings}"
    )


@pytest.mark.p0
@pytest.mark.settings
@pytest.mark.skip_version_before('v1.1.0')
def test_get_all_settings_v110(api_client, expected_settings):
    expected_settings = expected_settings['default'] | expected_settings['1.1.0']
    code, data = api_client.settings.get()

    available_settings = {m['metadata']['name'] for m in data['items']}

    assert 200 == code, (code, data)
    assert expected_settings <= available_settings, (
        "Some setting missing:\n"
        f"{expected_settings - available_settings}"
    )

    removed = expected_settings - available_settings
    added = available_settings - expected_settings

    if removed:
        warnings.warn(UserWarning(f"Few setting(s) been removed: {removed}."))
    if added:
        warnings.warn(UserWarning(f"New setting(s) added: {added}"))
