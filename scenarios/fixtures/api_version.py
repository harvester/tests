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

import pytest


@pytest.fixture(scope='session')
def harvester_api_version(request):
    # FIXME(gyee): we need to be able to discover this information from
    # the Harvester endpoint. Right now, all the Harvester endpoints are
    # protected.
    return 'harvesterhci.io/v1beta1'


@pytest.fixture(scope='session')
def cdi_api_version(request):
    # FIXME(gyee): we need to be able to discover this information from
    # the Harvester endpoint.
    return 'cdi.kubevirt.io/v1beta1'


@pytest.fixture(scope='session')
def kubevirt_api_version(request):
    # FIXME(gyee): we need to be able to discover this information from
    # the Harvester endpoint.
    return 'kubevirt.io/v1'
