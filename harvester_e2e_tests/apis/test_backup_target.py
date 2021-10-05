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
pytest_plugins = [
    'harvester_e2e_tests.fixtures.backuptarget'
]


def test_setup_backup_target_s3(backuptarget_s3):
    # NOTE: if the backuptarget is successfully create that means the
    # test is good
    pass


def test_setup_backup_target_nfs(backuptarget_nfs):
    # NOTE: if the backuptarget is successfully create that means the
    # test is good
    pass
