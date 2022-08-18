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

from io import StringIO
from paramiko import SSHClient, AutoAddPolicy, RSAKey
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from scp import SCPClient
import boto3
import jinja2
import json
import math
import os
import polling2
import random
import requests
import shutil
import string
import subprocess
import tempfile
import time
import uuid
import yaml
import re

UNITS = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
FRACTIONAL = ['', 'm', 'u', 'n', 'p', 'f', 'a', 'z', 'y']


def retry_session():
    """Create a session that will retry on connection errors"""
    # TODO(gyee): should we make retries and backoff_factor configurable?
    # We should retry on connection error only.
    # See https://urllib3.readthedocs.io/en/latest/reference/
    # urllib3.util.html#urllib3.util.Retry for more information.
    allowed_methods = frozenset({'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PUT',
                                 'TRACE', 'POST'})
    retry_strategy = Retry(total=5, backoff_factor=10.0,
                           status_forcelist=[500],
                           allowed_methods=allowed_methods)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    s = requests.Session()
    # TODO(gyee): do we need to support other auth methods?
    # NOTE(gyee): ignore SSL certificate validation for now
    s.verify = False
    s.mount('https://', adapter)
    s.mount('http://', adapter)
    return s


def random_name():
    """Generate a random alphanumeric name using uuid.uuid4()"""
    return uuid.uuid4().hex


def remove_ansicode(string):
    return re.sub(r"\x1b|\[\d+m", "", string)


def format_unit(value, *, increment=1000, start_exp=0, min_exp=0, max_exp=99,
                max_precision=2):
    # type: (int, int, int, int, int, int) -> str
    # https://github.com/harvester/dashboard/blob/master/shell/utils/units.js#L4

    val, exp, divide = value, start_exp, max_exp >= 0

    if divide:
        while exp < min_exp or (val >= increment and exp + 1 < len(UNITS)
                                and exp < max_exp):
            val = val / increment
            exp += 1
    else:
        while exp < (min_exp * -1) or (val < increment and exp + 1 < len(FRACTIONAL)
                                       and exp < (max_exp * -1)):
            val = val * increment
            exp += 1

    if val < 10 and max_precision >= 1:
        rv = f"{round(val * (10 ** max_precision) / (10 ** max_precision))}"
    else:
        rv = f"{round(val)}"

    return rv


def parse_unit(value):
    # https://github.com/harvester/dashboard/blob/master/shell/utils/units.js#L83
    try:
        pattern = r"^([0-9.-]+)\s*([^0-9.-]?)([^0-9.-]?)"
        val, unit, inc = re.match(pattern, value).groups()
        val = float(val)
        assert unit != ""
    except AttributeError:
        raise ValueError("Could not parse the value", value)
    except (AssertionError, ValueError):
        return val

    # µ (mu) symbol -> u
    unit = 'u' if ord(unit[0]) == 181 else unit

    divide = unit in FRACTIONAL
    multiply = unit.upper() in UNITS
    inc_base = 1024 if inc == 'i' and (divide or multiply) else 1000

    if divide:
        exp = FRACTIONAL.index(unit)
        return val / (inc_base ** exp)

    if multiply:
        exp = UNITS.index(unit.upper())
        return val * (inc_base ** exp)


def random_alphanumeric(length=5, upper_case=False):
    """Generate a random alphanumeric string of given length

    :param length: the size of the string
    :param upper_case: whether to return the upper case string
    """
    if upper_case:
        return ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(length))
    else:
        return ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(length))


def get_json_object_from_template(template_name, **template_args):
    """Load template from template file

    :param template_name: the name of the template. It is the filename of
                          template without the file extension. For example, if
                          you want to load './templates/foo.json.j2', then the
                          template_name should be 'foo'.
    :param template_args: dictionary of template argument values for the given
                          Jinja2 template
    """
    # get the current path relative to the ./templates/ directory
    my_path = os.path.dirname(os.path.realpath(__file__))
    # NOTE: the templates directory must be at the same level as
    # utilities.py, and all the templates must have the '.yaml.j2' extension
    templates_path = os.path.join(my_path, 'templates')
    template_file = f'{templates_path}/{template_name}.json.j2'
    # now load the template
    with open(template_file) as tempfile:
        template = jinja2.Template(tempfile.read())
    template.globals['random_name'] = random_name
    template.globals['random_alphanumeric'] = random_alphanumeric
    # now render the template
    rendered = template.render(template_args)
    return json.loads(rendered)


def poll_for_resource_ready(request, admin_session, endpoint,
                            expected_code=200):
    ready = polling2.poll(
        lambda: admin_session.get(endpoint).status_code == expected_code,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert ready, 'Timed out while waiting for %s to yield %s' % (
        endpoint, expected_code)


def get_latest_resource_version(request, admin_session, lookup_endpoint):
    poll_for_resource_ready(request, admin_session, lookup_endpoint)
    resp = admin_session.get(lookup_endpoint)
    assert resp.status_code == 200, 'Failed to lookup resource: %s' % (
        resp.content)
    return resp.json()['metadata']['resourceVersion']


def poll_for_update_resource(request, admin_session, update_endpoint,
                             request_json, lookup_endpoint, use_yaml=None):

    resp = None

    def _update_resource():
        # we want the update response to return back to the caller
        nonlocal resp

        # first we need to get the latest resourceVersion and fill that in
        # the request_json as it is a required field and must be the latest.
        request_json['metadata']['resourceVersion'] = (
            get_latest_resource_version(
                request, admin_session, lookup_endpoint))
        if use_yaml:
            resp = admin_session.put(update_endpoint,
                                     data=yaml.dump(
                                         request_json, sort_keys=False),
                                     headers={
                                         'Content-Type': 'application/yaml'})
        else:
            resp = admin_session.put(update_endpoint, json=request_json)
        if resp.status_code in [409, 500]:
            return False
        else:
            assert resp.status_code == 200, 'Failed to update resource: %s' % (
                resp.content)
            return True

    # NOTE(gyee): we need to do retries because kubenetes cluster does not
    # guarantee freshness when updating resources because of the way it handles
    # queuing. See
    # https://github.com/kubernetes/kubernetes/issues/84430
    # Therefore, we must do fetch-retry when updating resources.
    # Apparently this is way of life in Kubernetes world.
    updated = polling2.poll(
        _update_resource,
        step=3,
        timeout=120)
    assert updated, 'Timed out while waiting to update resource: %s' % (
        update_endpoint)
    return resp


def lookup_vm_instance(admin_session, harvester_api_endpoints, vm_json):
    # NOTE(gyee): seem like the corresponding VM instance has the same name as
    # the VM. If this assumption is not true, we need to fix this code.
    resp = admin_session.get(harvester_api_endpoints.get_vm_instance % (
        vm_json['metadata']['name']))
    assert resp.status_code == 200, 'Failed to lookup VM instance %s: %s' % (
        vm_json['metadata']['name'], resp.content)
    return resp.json()


def lookup_hosts_with_most_available_cpu(admin_session,
                                         harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_cpu_nodes = None
    most_available_cpu = 0
    for node in nodes_json:
        node_name = node['metadata']['name']
        r = node['metadata']['annotations']["management.cattle.io/pod-requests"]
        reserved = {k: parse_unit(v) for k, v in json.loads(r).items()
                    if k in ('cpu', 'memory')}

        available_cpu = int(node['status']['allocatable']['cpu']) - math.ceil(reserved['cpu'])
        if available_cpu > most_available_cpu:
            most_available_cpu = available_cpu
            most_available_cpu_nodes = [node_name]
        elif available_cpu == most_available_cpu:
            most_available_cpu_nodes.append(node_name)
    return (most_available_cpu_nodes, most_available_cpu)


def lookup_hosts_with_most_available_memory(admin_session,
                                            harvester_api_endpoints):
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    most_available_memory_nodes = None
    most_available_memory = 0
    exp = 3
    for node in nodes_json:
        node_name = node['metadata']['name']
        r = node['metadata']['annotations']["management.cattle.io/pod-requests"]
        reserved = {k: parse_unit(v) for k, v in json.loads(r).items()
                    if k in ('cpu', 'memory')}

        # NOTE: we want the floor here so we don't over commit
        max_memory = parse_unit(node['status']['allocatable']['memory']) * 0.99
        available_memory = math.floor(float(format_unit(max_memory - reserved['memory'],
                                                        increment=1024, min_exp=exp)))

        if available_memory > most_available_memory:
            most_available_memory = available_memory
            most_available_memory_nodes = [node_name]
        elif available_memory == most_available_memory:
            most_available_memory_nodes.append(node_name)

    return (most_available_memory_nodes, most_available_memory)


def lookup_hosts_with_cpu_and_memory(admin_session, harvester_api_endpoints,
                                     cpu, memory):
    """Lookup nodes that satisfies the given CPU and memory requirements"""
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    nodes = []
    for node in nodes_json:
        # look up CPU usage for the given node
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node['metadata']['name']))
        assert resp.status_code == 200, (
            'Failed to lookup metrices for node %s: %s' % (
                node['metadata']['name'], resp.content))
        metrics_json = resp.json()
        # NOTE: Kubernets CPU metrics are expressed in nanocores, or
        # 1 billionth of a CPU. We need to convert it to a whole CPU core.
        cpu_usage = math.ceil(
            int(metrics_json['usage']['cpu'][:-1]) / 1000000000)
        available_cpu = int(node['status']['allocatable']['cpu']) - cpu_usage
        # NOTE: Kubernets memory metrics are expressed Kibibyte so convert it
        # back to Gigabytes
        memory_usage = math.ceil(
            int(metrics_json['usage']['memory'][:-2]) * 1.024e-06)
        # NOTE: we want the floor here so we don't over commit
        allocatable_memory = int(node['status']['allocatable']['memory'][:-2])
        allocatable_memory = math.floor(
            allocatable_memory * 1.024e-06)
        available_memory = allocatable_memory - memory_usage
        if available_cpu >= cpu and available_memory >= memory:
            nodes.append(node['metadata']['name'])
    return nodes


def restart_vm(admin_session, harvester_api_endpoints, previous_uid, vm_name,
               wait_timeout):
    resp = admin_session.put(harvester_api_endpoints.restart_vm % (
        vm_name))
    assert resp.status_code == 202, 'Failed to restart VM instance %s: %s' % (
        vm_name, resp.content)
    assert_vm_restarted(admin_session, harvester_api_endpoints, previous_uid,
                        vm_name, wait_timeout)


def stop_vm(request, admin_session, harvester_api_endpoints,
            vm_name):
    resp = admin_session.put(harvester_api_endpoints.stop_vm % (
        vm_name))
    assert resp.status_code == 202, 'Failed to stop VM instance %s' % (
        vm_name)

    # give it some time for the VM instance to stop
    time.sleep(120)

    def _check_vm_instance_stopped():
        resp = admin_session.get(
            harvester_api_endpoints.get_vm_instance % (
                vm_name))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_vm_instance_stopped,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Failed to stop VM: %s' % (
        vm_name)


def assert_vm_restarted(admin_session, harvester_api_endpoints,
                        previous_uid, vm_name, wait_timeout):
    # give it some time for the VM instance to restart
    time.sleep(180)
    resp_json = dict()

    def _check_vm_instance_restarted():
        resp = admin_session.get(
            harvester_api_endpoints.get_vm_instance % (vm_name))
        if resp.status_code == 200:
            nonlocal resp_json
            resp_json = resp.json()
            if (resp_json.get('status', {}).get('phase') == "Running"
                    and resp_json['metadata']['uid'] != previous_uid):
                return True
        return False

    try:
        polling2.poll(
            _check_vm_instance_restarted,
            step=5,
            timeout=wait_timeout)
    except polling2.TimeoutException:
        raise AssertionError(f'Failed to restart VM {vm_name}\n'
                             f"previous uid: {previous_uid}, "
                             f"current uid: {resp_json['metadata']['uid']}\n"
                             f"VM's Phase: {resp_json.get('status', {}).get('phase')}")


def delete_image(request, admin_session, harvester_api_endpoints, image_json):
    delete_image_by_name(request,
                         admin_session,
                         harvester_api_endpoints,
                         image_json['metadata']['name'])


def delete_image_by_name(request, admin_session,
                         harvester_api_endpoints, image_name):
    # see if the image exist first
    resp = admin_session.get(harvester_api_endpoints.get_image % (image_name))
    if resp.status_code == 404:
        # image doesn't exist so nothing to be done
        return

    def _wait_for_image_to_be_deleted():
        # retry delete
        admin_session.delete(harvester_api_endpoints.delete_image %
                             (image_name))
        time.sleep(15)
        resp = admin_session.get(harvester_api_endpoints.get_image %
                                 (image_name))
        if resp.status_code == 404:
            return True
        return False

    try:
        polling2.poll(
            _wait_for_image_to_be_deleted,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
    except polling2.TimeoutException:
        errmsg = 'Timed out while waiting for image to be deleted'
        raise AssertionError(errmsg)


def assert_image_ready(request, admin_session,
                       harvester_api_endpoints, image_name):

    resp = admin_session.get(harvester_api_endpoints.get_image % (image_name))
    if resp.status_code == 404:
        raise AssertionError(f"Image ${image_name} not exists")

    resp_json = dict()

    def _check_image_ready():
        resp = admin_session.get(harvester_api_endpoints.get_image %
                                 (image_name))
        nonlocal resp_json
        resp_json = resp.json()
        if resp_json['status'].get("progress", 0) == 100:
            return True

        status = resp_json['status']
        if status['conditions'][0].get("reason") == "ImportFailed":
            reason = status['conditions'][0]['message']
            raise AssertionError(f"Image import Failed with reason: {reason}")

        return False

    try:
        polling2.poll(
            _check_image_ready,
            step=5,
            timeout=request.config.getoption("--wait-timeout"))
    except polling2.TimeoutException:
        errmsg = ("Timed out while waiting for image to be ready\n"
                  f"Stucking in the status {resp_json['status']}")
        raise AssertionError(errmsg)


def create_image(request, admin_session, harvester_api_endpoints, url,
                 name=None, description='', source_type='download'):
    request_json = get_json_object_from_template(
        'basic_image',
        name=name,
        source_type=source_type,
        description=description,
        url=url
    )
    resp = admin_session.post(harvester_api_endpoints.create_image,
                              json=request_json)
    assert resp.status_code in [200, 201], 'Failed to create image %s: %s' % (
        name, resp.content)
    image_json = resp.json()

    # wait for the image to get ready
    time.sleep(50)

    def _wait_for_image_become_active():
        # we want the update response to return back to the caller
        nonlocal image_json

        resp = admin_session.get(harvester_api_endpoints.get_image % (
            image_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to get image %s: %s' % (
            image_json['metadata']['name'], resp.content)
        image_json = resp.json()
        if ('status' in image_json and
                'storageClassName' in image_json['status']):
            return True
        return False

    success = polling2.poll(
        _wait_for_image_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be active.'

    return image_json


def assert_vm_unschedulable(request, admin_session, harvester_api_endpoints,
                            vm_name):
    # give it some time for the scheduler to find a host
    time.sleep(120)

    def _check_vm_instance_unschedulable():
        resp = admin_session.get(
            harvester_api_endpoints.get_vm_instance % (vm_name))
        if resp.status_code == 200:
            resp_json = resp.json()
            if ('status' in resp_json and
                    'conditions' in resp_json['status']):
                for condition in resp_json['status']['conditions']:
                    if ('reason' in condition and
                            condition['reason'] == 'Unschedulable'):
                        return True
        return False

    success = polling2.poll(
        _check_vm_instance_unschedulable,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, (
        'Timed out while waiting for the %s instance to become '
        'unscheduable' % (vm_name))


def assert_vm_ready(request, admin_session, harvester_api_endpoints,
                    vm_name, running):
    # give it some time for the VM to boot up
    time.sleep(180)
    resp_json = dict()

    def _check_vm_ready():
        resp = admin_session.get(harvester_api_endpoints.get_vm_instance %
                                 (vm_name))
        if resp.status_code == 200:
            nonlocal resp_json
            resp_json = resp.json()
            if running:
                if ('status' in resp_json and
                        'phase' in resp_json['status'] and
                        'Running' in resp_json['status']['phase'] and
                        'nodeName' in resp_json['status']):
                    return True
            else:
                if ('status' in resp_json and
                        'Running' not in resp_json['status']['phase']):
                    return True
        return False

    try:
        polling2.poll(
            _check_vm_ready,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
    except polling2.TimeoutException:
        errmsg = ('Timed out while waiting for VM to be ready.\n'
                  f"Stucking in Phase {resp_json['status']['phase']}")
        raise AssertionError(errmsg)


def create_vm(request, admin_session, image, harvester_api_endpoints,
              template='basic_vm', keypair=None, volume=None, network=None,
              cpu=1, disk_size_gb=10, memory_gb=1, network_data=None,
              user_data=None, running=True, machine_type='q35',
              include_usb=True):
    volume_name = None
    ssh_public_key = None
    network_name = None
    if network:
        network_name = network['metadata']['name']
    if volume:
        volume_name = volume['metadata']['name']
    if keypair:
        ssh_public_key = keypair['spec']['publicKey']
    request_json = get_json_object_from_template(
        template,
        image_namespace=image['metadata']['namespace'],
        image_name=image['metadata']['name'],
        image_storage_class=image['status']['storageClassName'],
        volume_name=volume_name,
        network_name=network_name,
        disk_size_gb=disk_size_gb,
        cpu=cpu,
        memory_gb=memory_gb,
        ssh_public_key=ssh_public_key,
        network_data=network_data,
        user_data=user_data,
        machine_type=machine_type,
        include_usb=include_usb
    )

    request_json['spec']['runStrategy'] = "RerunOnFailure" if running else "Halted"

    resp = admin_session.post(harvester_api_endpoints.create_vm,
                              json=request_json)
    assert resp.status_code == 201, (
        'Failed to create VM %s: %s' % (resp.status_code, resp.content))
    vm_resp_json = resp.json()
    if running:
        assert_vm_ready(request, admin_session, harvester_api_endpoints,
                        vm_resp_json['metadata']['name'], running)
    return vm_resp_json


def delete_vm(request, admin_session, harvester_api_endpoints, vm_json,
              remove_all_disks=True):
    resp = admin_session.delete(harvester_api_endpoints.delete_vm % (
        vm_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Failed to delete VM %s: %s' % (
        vm_json['metadata']['name'], resp.content)

    def _check_vm_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_vm % (
            vm_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_vm_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for VM to be terminated.'
    if remove_all_disks:
        # NOTE: for PVC, we must explicitly delete the volumes after the
        # VM is deleted
        volumes = vm_json['spec']['template']['spec']['volumes']
        for volume in volumes:
            if 'persistentVolumeClaim' in volume:
                delete_volume_by_name(
                    request, admin_session, harvester_api_endpoints,
                    volume['persistentVolumeClaim']['claimName'],
                    owned_by=vm_json['metadata']['name'])


def delete_volume(request, admin_session, harvester_api_endpoints,
                  volume_json):
    delete_volume_by_name(request, admin_session, harvester_api_endpoints,
                          volume_json['metadata']['name'])


def delete_volume_by_name(request, admin_session, harvester_api_endpoints,
                          volume_name, owned_by=None):
    # see if the volume exist first
    resp = admin_session.get(harvester_api_endpoints.get_volume % (
        volume_name))
    if resp.status_code == 404:
        # volume doesn't exist so nothing to be done
        return

    def _wait_for_vm_remove_owned_by():
        if owned_by is None:
            return True
        resp = admin_session.get(harvester_api_endpoints.get_volume % (
            volume_name))
        volume_json = resp.json()
        annotations = volume_json['metadata']['annotations']
        if 'harvesterhci.io/owned-by' in annotations:
            if owned_by in annotations['harvesterhci.io/owned-by']:
                return False
            return True
        else:
            return True

    success = polling2.poll(
        _wait_for_vm_remove_owned_by,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))

    resp = admin_session.delete(harvester_api_endpoints.delete_volume % (
        volume_name))
    assert resp.status_code in [200, 201], (
        'Failed to delete volume %s: %s' % (volume_name, resp.content))

    def _check_volume_deleted():
        resp = admin_session.get(harvester_api_endpoints.delete_volume % (
            volume_name))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _check_volume_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for volume to be terminated.'


def delete_host(request, admin_session, harvester_api_endpoints, host_json):
    resp = admin_session.delete(harvester_api_endpoints.delete_node % (
        host_json['id']))
    assert resp.status_code in [200, 201], 'Unable to delete host %s: %s' % (
        host_json['id'], resp.content)
    # wait for host to be deleted
    time.sleep(180)

    def _wait_for_host_to_be_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_node % (
            host_json['id']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_host_to_be_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for host to be deleted'


def _get_node_script_path(request, script_name=None, script_type=None):
    if script_type == 'terraform':
        scripts_dir = request.config.getoption('--terraform-scripts-location')
    elif script_type == 'backup':
        scripts_dir = request.config.getoption('--backup-scripts-location')
    else:
        scripts_dir = request.config.getoption('--node-scripts-location')
    assert scripts_dir, ('Node scripts location not provided. Please use '
                         'the --node-scripts-location parameter to specify '
                         'the location of the node scripts.')
    assert os.path.isdir(scripts_dir), 'Invalid node scripts location: %s' % (
        scripts_dir)
    script = scripts_dir
    if script_name:
        script = os.path.join(scripts_dir, script_name)
        assert os.path.isfile(script), 'Node script %s not found' % (script)
        assert os.access(script, os.X_OK), 'Node script %s not executable' % (
            script)
    return script


def _lookup_node_ip(admin_session, harvester_api_endpoints, node_name):
    resp = admin_session.get(harvester_api_endpoints.get_node % (node_name))
    assert resp.status_code == 200, 'Failed to lookup host %s: %s' % (
        node_name, resp.content)
    node_json = resp.json()
    for address in node_json['status']['addresses']:
        if address['type'] == 'InternalIP':
            return address['address']
    assert False, 'Failed to lookup host IP: %s' % (
        node_json['status']['addresses'])


def power_off_node(request, admin_session, harvester_api_endpoints, node_name,
                   node_ip=None):
    power_off_script = _get_node_script_path(request, 'power_off.sh')
    if node_ip is None:
        node_ip = _lookup_node_ip(admin_session, harvester_api_endpoints,
                                  node_name)
    result = subprocess.run([power_off_script, node_name, node_ip],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, (
        'Failed to power-off node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to disappear
    time.sleep(120)

    def _wait_for_node_to_disappear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if 'status' in metrics_json and metrics_json['status'] == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_disappear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to shutdown'


def power_on_node(request, admin_session, harvester_api_endpoints, node_name,
                  node_ip=None):
    power_on_script = _get_node_script_path(request, 'power_on.sh')
    if node_ip is None:
        node_ip = _lookup_node_ip(admin_session, harvester_api_endpoints,
                                  node_name)
    result = subprocess.run([power_on_script, node_name, node_ip],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, (
        'Failed to power-on node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to power-on
    time.sleep(180)

    def _wait_for_node_to_appear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if ('metadata' in metrics_json and
                'state' in metrics_json['metadata'] and
                metrics_json['metadata']['state']['error'] is False):
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_appear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to power-on'


def lookup_host_not_harvester_endpoint(request, admin_session,
                                       harvester_api_endpoints):
    cur_endpoint = (request.config.getoption('--endpoint').split(":")[1])[2:]
    resp = admin_session.get(harvester_api_endpoints.list_nodes)
    assert resp.status_code == 200, 'Failed to list nodes: %s' % (resp.content)
    nodes_json = resp.json()['data']
    for node in nodes_json:
        # look up CPU usage for the given node
        if node['metadata']['annotations'].get(
                'etcd.k3s.cattle.io/node-address') != cur_endpoint:
            node_data = node
    return node_data


def reboot_node(request, admin_session, harvester_api_endpoints, node_name,
                node_ip=None):
    reboot_script = _get_node_script_path(request, 'reboot.sh')
    if node_ip is None:
        node_ip = _lookup_node_ip(admin_session, harvester_api_endpoints,
                                  node_name)
    result = subprocess.run([reboot_script, node_name, node_ip],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, (
        'Failed to reboot node %s: rc: %s, stdout: %s, stderr: %s' % (
            node_name, result.returncode, result.stderr, result.stdout))

    # wait for the node to power-on
    time.sleep(180)

    def _wait_for_node_to_appear():
        resp = admin_session.get(harvester_api_endpoints.get_node_metrics % (
            node_name))
        metrics_json = resp.json()
        if ('metadata' in metrics_json and
                'state' in metrics_json['metadata'] and
                metrics_json['metadata']['state']['error'] is False):
            return True
        return False

    success = polling2.poll(
        _wait_for_node_to_appear,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for node to reboot'


def poweroff_host_maintenance_mode(request, admin_session,
                                   harvester_api_endpoints):
    host_poweroff = lookup_host_not_harvester_endpoint(request, admin_session,
                                                       harvester_api_endpoints)
    # Enable Maintenance Mode
    enable_maintenance_mode(request, admin_session,
                            harvester_api_endpoints, host_poweroff)
    node_name = host_poweroff['id']
    poll_for_resource_ready(request, admin_session,
                            harvester_api_endpoints.get_node % (node_name))
    resp = admin_session.get(
        harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert ret_data["spec"]["unschedulable"]
    s = ret_data["metadata"]["annotations"]["harvesterhci.io/maintain-status"]
    assert s in ["running", "completed"]
    node_name = host_poweroff['id']
    # Power Off Node
    power_off_node(request, admin_session, harvester_api_endpoints,
                   node_name)
    resp = admin_session.get(
        harvester_api_endpoints.get_node % (node_name))
    resp.status_code == 200, 'Failed to get host: %s' % (resp.content)
    ret_data = resp.json()
    assert "NotReady,SchedulingDisabled" in ret_data["metadata"]["fields"]
    return host_poweroff


def enable_maintenance_mode(request, admin_session, harvester_api_endpoints,
                            node_json):

    def _add_drain_taint(node_json):
        if 'taints' in node_json['spec']:
            for taint in node_json['spec']['taints']:
                if taint['key'] == 'kubevirt.io/drain':
                    return
        else:
            node_json['spec']['taints'] = []
        node_json['spec']['taints'].append(
            {
                'key': 'kubevirt.io/drain',
                'value': 'scheduling',
                'effect': 'NoSchedule'
            }
        )

    # NOTE(gyee): implemention of
    # https://github.com/harvester/harvester/blob/
    # 3edc82a7ae6a5de6e8114901058dc573938093e8/pkg/api/node/formatter.go#L92
    node_json['spec']['unschedulable'] = True
    _add_drain_taint(node_json)
    if 'annotations' not in node_json['metadata']:
        node_json['metadata']['annotations'] = {}
    node_json['metadata']['annotations']['harvesterhci.io/maintain-status'] = (
        'running')
    poll_for_update_resource(request, admin_session,
                             node_json['links']['update'],
                             node_json,
                             harvester_api_endpoints.get_node % (
                                 node_json['metadata']['name']))


def disable_maintenance_mode(request, admin_session, harvester_api_endpoints,
                             node_json):
    # NOTE(gyee): implementation of
    # https://github.com/harvester/harvester/blob/
    # 3edc82a7ae6a5de6e8114901058dc573938093e8/pkg/api/node/formatter.go#L118
    node_json['spec']['unschedulable'] = False
    if 'taints' in node_json['spec']:
        node_json['spec']['taints'] = [
            t for t in node_json['spec']['taints'] if not (
                t['key'] == 'kubevirt.io/drain')]
    del node_json['metadata']['annotations']['harvesterhci.io/maintain-status']
    poll_for_update_resource(request, admin_session,
                             node_json['links']['update'],
                             node_json,
                             harvester_api_endpoints.get_node % (
                                 node_json['metadata']['name']))


def create_tf_from_template(request, template_name, **template_args):
    # get the current path relative to the ./templates/ directory
    my_path = os.path.dirname(os.path.realpath(__file__))
    # NOTE: the templates directory must be at the same level as
    # utilities.py, and all the templates must have the '.yaml.j2' extension
    templates_path = os.path.join(my_path, 'templates')
    template_file = f'{templates_path}/{template_name}.tf.j2'
    # now load the template
    with open(template_file) as tempfile:
        template = jinja2.Template(tempfile.read())
    # now render the template
#    template.globals['random_name'] = random_name
    rendered = template.render(template_args)
    tf_file_dir = _get_node_script_path(request, script_type='terraform')
    tf_file_path = os.path.join(tf_file_dir, f'{template_name}.tf')
    with open(tf_file_path, 'w') as f:
        f.write(rendered)


def create_kubeconfig_from_template(request, template_name, **template_args):
    # Create/Update kubeconfig
    my_path = os.path.dirname(os.path.realpath(__file__))
    # NOTE: the templates directory must be at the same level as
    # utilities.py, and all the templates must have the '.yaml.j2' extension
    templates_path = os.path.join(my_path, 'templates')
    template_file = f'{templates_path}/{template_name}.j2'
    with open(template_file) as tempfile:
        template = jinja2.Template(tempfile.read())
    # now render the template
    rendered = template.render(template_args)
    terraform_path = _get_node_script_path(
        request, script_type='terraform')
    kubeconfig_dir = os.path.join(terraform_path, '.kube')
    if not os.path.exists(kubeconfig_dir):
        os.makedirs(kubeconfig_dir)
    config_file_path = os.path.join(kubeconfig_dir, 'config')
    with open(config_file_path, 'w') as f:
        f.write(rendered)
    create_tf_from_template(
        request,
        'provider',
        kubeconfig=os.path.abspath(config_file_path))


def create_image_terraform(request, admin_session, harvester_api_endpoints,
                           url):
    name = "t-" + random_name()
    create_tf_from_template(
        request,
        'resource_image',
        name=name,
        url=url)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_script = _get_node_script_path(
        request, 'terraform.sh', 'terraform')
    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))
    # wait for the image to get ready
    time.sleep(50)

    def _wait_for_image_become_active():
        # we want the update response to return back to the caller

        resp = admin_session.get(harvester_api_endpoints.get_image % (
            name))
        assert resp.status_code == 200, 'Failed to get image %s: %s' % (
            name, resp.content)
        image_json = resp.json()
        if ('status' in image_json and
                'storageClassName' in image_json['status'] and
                'progress' in image_json['status'] and
                image_json['status']['progress'] == 100):
            return True
        return False

    success = polling2.poll(
        _wait_for_image_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for image to be active.'

    resp = admin_session.get(harvester_api_endpoints.get_image % (
        name))
    image_json = resp.json()
    return image_json


def destroy_resource(request, admin_session, destroy_type=None):
    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_path = _get_node_script_path(
        request, script_type='terraform')
    if os.path.isdir(os.path.join(terraform_path, 'terraformharvester')):
        terraform_script = _get_node_script_path(
            request, 'terraform_destroy.sh', 'terraform') + ' ' + destroy_type
        result = subprocess.run([terraform_script], shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result.stdout = remove_ansicode(result.stdout.decode())
        result.stderr = remove_ansicode(result.stderr.decode())

        assert result.returncode == 0, (
            'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
                result.returncode, result.stderr, result.stdout))

    if os.path.isdir(os.path.join(terraform_path, '.kube')):
        shutil.rmtree(os.path.join(terraform_path, '.kube'))

    if os.path.isfile(os.path.join(terraform_path, 'provider.tf')):
        os.remove(os.path.join(terraform_path, 'provider.tf'))


def create_volume_terraform(request, admin_session, harvester_api_endpoints,
                            template_name, size, image=None):
    name = "t-" + random_name()
    create_tf_from_template(
        request,
        template_name,
        name=name,
        size=size,
        image=image)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_script = _get_node_script_path(
        request, 'terraform.sh', 'terraform')
    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))

    resp = admin_session.get(harvester_api_endpoints.get_volume % (
        name))
    assert resp.status_code == 200, 'Failed to get Volume %s: %s' % (
        name, resp.content)

    vol_data = resp.json()
    return vol_data


def create_keypair_terraform(request, admin_session, harvester_api_endpoints,
                             template_name, public_key):
    name = "t-" + random_name()
    create_tf_from_template(
        request,
        template_name,
        name=name,
        public_key=public_key)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_script = _get_node_script_path(
        request, 'terraform.sh', 'terraform')
    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))

    resp = admin_session.get(harvester_api_endpoints.get_keypair % (
        name))
    assert resp.status_code == 200, 'Failed to get Volume %s: %s' % (
        name, resp.content)

    keypair_data = resp.json()
    return keypair_data


def create_network_terraform(request, admin_session, harvester_api_endpoints,
                             template_name, vlan_id, import_flag):

    # NOTE(gyee): will name the network with the following convention as
    # VLAN ID must be unique. vlan_network_<VLAN ID>
    name = f'vlan-network-{vlan_id}'
    create_tf_from_template(
        request,
        template_name,
        name=name,
        vlan_id=vlan_id)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    if import_flag:
        terraform_script = _get_node_script_path(
            request, 'terraform.sh', 'terraform') + \
                           ' ' + 'network' + ' ' + name
    else:
        terraform_script = _get_node_script_path(
            request, 'terraform.sh', 'terraform')

    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))

    poll_for_resource_ready(request, admin_session,
                            harvester_api_endpoints.get_network % (name))
    resp = admin_session.get(harvester_api_endpoints.get_network % (
        name))
    assert resp.status_code == 200, 'Failed to get Network %s: %s' % (
        name, resp.content)

    network_data = resp.json()
    return network_data


def create_clusternetworks_terraform(request, admin_session,
                                     harvester_api_endpoints,
                                     template_name,
                                     vlan_nic=None):

    create_tf_from_template(
        request,
        template_name,
        vlan_nic=vlan_nic)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_script = _get_node_script_path(
        request, 'terraform.sh', 'terraform') + ' ' + 'cluster'
    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))

    poll_for_resource_ready(request, admin_session,
                            harvester_api_endpoints.get_vlan)
    resp = admin_session.get(harvester_api_endpoints.get_vlan)
    assert resp.status_code == 200, 'Failed to get vlan: %s' % (resp.content)
    network_data = resp.json()
    return network_data


def create_vm_terraform(request, admin_session, harvester_api_endpoints,
                        template_name,
                        keypair=None,
                        image=None,
                        volume=None,
                        net=None,
                        user_data=None,
                        net_data=None):
    name = 't-' + random_name()
    create_tf_from_template(
        request,
        template_name,
        name=name,
        image_name=image['metadata']['name'],
        vol_name=volume['metadata']['name'],
        net_name=net['metadata']['name'],
        keypair=keypair['metadata']['name'],
        public_key=keypair['spec']['publicKey'],
        user_data=user_data,
        net_data=net_data)

    create_kubeconfig_from_template(
        request,
        'kube_config',
        harvester_endpoint=request.config.getoption('--endpoint'),
        token=(admin_session.headers['authorization']).split()[1]
    )

    terraform_script = _get_node_script_path(
        request, 'terraform.sh', 'terraform')
    result = subprocess.run([terraform_script], shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result.stdout = remove_ansicode(result.stdout.decode())
    result.stderr = remove_ansicode(result.stderr.decode())

    assert result.returncode == 0, (
        'Failed to run terraform : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))

    assert_vm_ready(request, admin_session, harvester_api_endpoints,
                    name, running=True)
    resp = admin_session.get(harvester_api_endpoints.get_vm % (
        name))
    assert resp.status_code == 200, 'Failed to get VirtualMachine %s: %s' % (
        name, resp.content)

    vm_data = resp.json()
    return vm_data


def create_image_upload(request, admin_session, harvester_api_endpoints,
                        name=None):

    cache_url = request.config.getoption('--image-cache-url')

    base_url = ('http://download.opensuse.org/repositories/Cloud:/Images:/'
                'Leap_15.2/images')
    if cache_url:
        base_url = cache_url
    url = os.path.join(base_url, 'openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')

    with tempfile.TemporaryDirectory() as tmpdir:
        image_path = os.path.join(
            tmpdir, 'openSUSE-Leap-15.2.x86_64-NoCloud.qcow2')
        # first download the file
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(image_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        # create an image for upload
        image_json = create_image(request, admin_session,
                                  harvester_api_endpoints,
                                  '', source_type='upload')
        image_name = image_json['metadata']['name']
        # now upload the file in one shot
        # TODO(gyee): need to check with Harvester team to see if the API
        # supports streaming
        image_size = os.stat(image_path).st_size
        files = {'chunk': open(image_path, 'rb')}
        params = {'action': 'upload',
                  'size': image_size}
        resp = admin_session.post(
            harvester_api_endpoints.upload_image % (image_name),
            files=files,
            params=params)
        assert resp.status_code in [200, 201], (
            'Failed to upload image %s: %s: %s' % (
                image_name, resp.status_code, resp.content))

        def _wait_for_image_upload_complete():
            # we want the update response to return back to the caller
            nonlocal image_json

            resp = admin_session.get(harvester_api_endpoints.get_image % (
                image_json['metadata']['name']))
            assert resp.status_code == 200, 'Failed to get image %s: %s' % (
                image_json['metadata']['name'], resp.content)
            image_json = resp.json()
            if ('status' in image_json and
                    'progress' in image_json['status'] and
                    'size' in image_json['status'] and
                    image_json['status']['progress'] == 100 and
                    image_json['status']['size'] == image_size):
                return True
            return False

        success = polling2.poll(
            _wait_for_image_upload_complete,
            step=5,
            timeout=request.config.getoption('--wait-timeout'))
        assert success, 'Timed out while waiting for image upload to finish.'

    return image_json


def is_marker_enabled(request, marker_name):
    for item in request.session.items:
        if item.get_closest_marker(marker_name) is not None:
            return True
    return False


def create_vm_backup(request, admin_session, harvester_api_endpoints,
                     backuptarget, name=None, vm_name=None):
    request_json = get_json_object_from_template(
        'basic_vm_backup',
        name=name,
        vm_name=vm_name
    )
    backuptarget_value = json.loads(backuptarget['value'])
    backuptarget_type = backuptarget_value['type']
    if backuptarget_type == 's3':
        total_objects_before_backup = get_total_objects_s3_bucket(request)
    else:
        total_objects_before_backup = get_total_objects_nfs_share(request)

    resp = admin_session.post(harvester_api_endpoints.create_vm_backup,
                              json=request_json)
    assert resp.status_code in [200, 201], 'Failed to create backup %s: %s' % (
        name, resp.content)
    backup_json = resp.json()

    # wait for the backup to get ready
    time.sleep(30)

    def _wait_for_backup_become_active():
        # we want the update response to return back to the caller

        resp = admin_session.get(harvester_api_endpoints.get_vm_backup % (
            backup_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to get backup %s: %s' % (
            backup_json['metadata']['name'], resp.content)
        resp_json = resp.json()
        if ('status' in resp_json and
                'readyToUse' in resp_json['status'] and
                resp_json['status']['readyToUse']):
            return True
        return False

    success = polling2.poll(
        _wait_for_backup_become_active,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Failed to Backup  VM: %s' % (
        vm_name)

    if backuptarget_type == 's3':
        total_objects_after_backup = get_total_objects_s3_bucket(request)
    else:
        total_objects_after_backup = get_total_objects_nfs_share(request)

    time.sleep(50)

    assert total_objects_before_backup < total_objects_after_backup, (
        'Failed to add any objects in %s target. '
        'Before backup object count: %s; after backup object count: %s' % (
            backuptarget_type, total_objects_before_backup,
            total_objects_after_backup))
    return backup_json


def delete_vm_backup(request, admin_session,
                     harvester_api_endpoints, backuptarget, backup_json):

    backuptarget_value = json.loads(backuptarget['value'])
    backuptarget_type = backuptarget_value['type']
    if backuptarget_type == 's3':
        total_objects_before_delete = get_total_objects_s3_bucket(request)
    else:
        total_objects_before_delete = get_total_objects_nfs_share(request)
    resp = admin_session.delete(harvester_api_endpoints.delete_vm_backup % (

        backup_json['metadata']['name']))
    assert resp.status_code in [200, 201], 'Unable to del backup %s: %s' % (
        backup_json['metadata']['name'], resp.content)

    def _wait_for_backup_to_be_deleted():
        resp = admin_session.get(harvester_api_endpoints.get_vm_backup % (
            backup_json['metadata']['name']))
        if resp.status_code == 404:
            return True
        return False

    success = polling2.poll(
        _wait_for_backup_to_be_deleted,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Timed out while waiting for backup to be deleted'

    time.sleep(50)
    if backuptarget_type == 's3':
        total_objects_after_delete = get_total_objects_s3_bucket(request)
    else:
        total_objects_after_delete = get_total_objects_nfs_share(request)

    assert total_objects_before_delete > total_objects_after_delete, (
        'Failed to delete any objects from %s target. '
        'Before delete object count: %s; after delete object count: %s' % (
            backuptarget_type, total_objects_before_delete,
            total_objects_after_delete))


def get_total_objects_s3_bucket(request):
    accesskey = request.config.getoption('--accessKeyId')
    secretaccesskey = request.config.getoption('--secretAccessKey')
    bucket = request.config.getoption('--bucketName')
    region = request.config.getoption('--region')
    totalCount = 0
    s3 = boto3.resource("s3",
                        region_name=region,
                        aws_access_key_id=accesskey,
                        aws_secret_access_key=secretaccesskey)
    s3bucket = s3.Bucket(bucket)
    for key in s3bucket.objects.all():
        totalCount += 1

    return totalCount


def get_total_objects_nfs_share(request):
    backup_script = get_backup_create_files_script(
        request, 'mountnfs.sh', 'backup')
    nfsendpoint = (request.config.getoption('--nfs-endpoint').split("//")[1])
    nfsmountdir = request.config.getoption('--nfs-mount-dir')
    total_objects = 0
    result = subprocess.run([backup_script, nfsendpoint, nfsmountdir],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0, (
        'Failed to run mountnfs : rc: %s, stdout: %s, stderr: %s' % (
            result.returncode, result.stderr, result.stdout))
    total_objects = int(result.stdout.decode("utf-8"))
    return total_objects


def restore_vm_backup(request, admin_session, harvester_api_endpoints,
                      name=None, vm_name=None,
                      backup_name=None, vm_new=None):
    request_json = get_json_object_from_template(
        'basic_vm_restore',
        name=name,
        vm_name=vm_name,
        backup_name=backup_name
    )
    if vm_new:
        request_json['spec']['newVM'] = vm_new
    resp = admin_session.post(harvester_api_endpoints.create_vm_restore,
                              json=request_json)
    assert resp.status_code in [200, 201], 'Failed to restore bakup %s: %s' % (
        backup_name, resp.content)
    restore_json = resp.json()

    # wait for the restore to get ready
    time.sleep(30)

    def _wait_for_restore_to_finish():
        # we want the update response to return back to the caller

        resp = admin_session.get(harvester_api_endpoints.get_vm_restore % (
            restore_json['metadata']['name']))
        assert resp.status_code == 200, 'Failed to restore %s: %s' % (
            restore_json['metadata']['name'], resp.content)
        resp_json = resp.json()
        if ('status' in resp_json and
                'complete' in resp_json['status'] and
                resp_json['status']['complete']):
            return True
        return False

    success = polling2.poll(
        _wait_for_restore_to_finish,
        step=5,
        timeout=request.config.getoption('--wait-timeout'))
    assert success, 'Failed to Restore  VM: %s' % (
        vm_name)

    return restore_json


def get_backup_create_files_script(request,
                                   script_name=None,
                                   script_type=None):
    script = _get_node_script_path(request, script_name, script_type)
    return script


def wait_for_ssh_client(ip, timeout, keypair=None):
    client = SSHClient()
    # automatically add host since we only care about connectivity
    client.set_missing_host_key_policy(AutoAddPolicy)

    def _wait_for_connect():
        try:
            # NOTE: for the default openSUSE Leap image, the root user
            # password is 'linux'
            if keypair is not None:
                private_key = RSAKey.from_private_key(
                    StringIO(keypair['spec']['privateKey']))
                client.connect(ip, username='root', pkey=private_key)
            else:
                client.connect(ip, username='root', password='linux')
        except Exception as e:
            print('Unable to connect to %s: %s' % (ip, e))
            return False
        return True

    ready = polling2.poll(
        _wait_for_connect,
        step=5,
        timeout=timeout)
    assert ready, 'Timed out while waiting for SSH server to be ready'
    return client


def get_vm_ip_address(admin_session, harvester_api_endpoints, vm, timeout,
                      nic_name='default'):
    vm_instance_json = None

    def _wait_for_ip():
        nonlocal vm_instance_json
        vm_instance_json = lookup_vm_instance(
            admin_session, harvester_api_endpoints, vm)
        for interface in vm_instance_json['status']['interfaces']:
            # NOTE: by default, the second NIC name is 'nic-1'
            if (interface['name'] == nic_name and
                    'ipAddress' in interface):
                return interface['ipAddress']

    try:
        ip = polling2.poll(_wait_for_ip, step=5, timeout=timeout)
    except polling2.TimeoutException:
        errmsg = ('Timed out while waiting for IP address for NIC %s to be '
                  ' assigned: %s' % (nic_name, vm_instance_json))
        raise AssertionError(errmsg)

    return (vm_instance_json, ip)


def execute_script_on_vm(ip, timeout, script, keypair=None,
                         script_params=None):
    ssh_client = wait_for_ssh_client(ip, timeout, keypair)
    # first copy the script to the /tmp dir on the VM
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.put(script, '/tmp')
    # now execute the script on the VM and return stdout as string
    command = 'bash /tmp/%s' % (os.path.basename(script))
    if script_params:
        command += ' ' + script_params
    stdin, stdout, stderr = ssh_client.exec_command(command)
    ssh_client.close()
    errors = stderr.read().strip().decode('utf-8')
    assert not errors, (
        'Failed to execute %s on %s: %s' % (script, ip, errors))
    return stdout.read().strip().decode('utf-8')
