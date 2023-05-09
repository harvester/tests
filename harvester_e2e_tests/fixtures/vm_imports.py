# Copyright (c) 2023 SUSE LLC
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
from harvester_e2e_tests import utils
import pytest
import os

from datetime import datetime, timedelta
from time import sleep


@pytest.fixture(scope='module')
def user_data_openstack():
    # set to root user password to 'linux' to test password login in
    # addition to SSH login
    yaml_data = """#cloud-config
chpasswd:
  list: |
    root:linux
  expire: false
ssh_pwauth: true
users:
  - name: root
package_update: true
packages:
  - qemu-guest-agent
snap:
  commands:
    - snap install microstack --devmode --beta
    - snap alias microstack.openstack openstack
    - snap set microstack config.credentials.keystone-password=testtesttest
runcmd:
  - - systemctl
    - enable
    - '--now'
    - qemu-ga
  - echo fs.inotify.max_queued_events=1048576 | tee -a /etc/sysctl.conf
  - echo fs.inotify.max_user_instances=1048576 | tee -a /etc/sysctl.conf
  - echo fs.inotify.max_user_watches=1048576 | tee -a /etc/sysctl.conf
  - echo vm.max_map_count=262144 | tee -a /etc/sysctl.conf
  - echo vm.swappiness=1 | tee -a /etc/sysctl.conf
  - sysctl -p
  - microstack init --auto --control --setup-loop-based-cinder-lvm-backend --loop-device-file-size 50
  - snap restart microstack.cinder-{uwsgi,scheduler,volume}
"""
    return yaml_data.replace('\n', '\\n')
