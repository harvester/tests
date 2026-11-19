import json
import ssl
from datetime import datetime, timedelta
from time import sleep
from urllib.parse import urlparse

import pytest
import requests

pytest_plugins = [
    "harvester_e2e_tests.fixtures.api_client",
]

DISPLAY_NAME = "harvesterhci.io/vmDisplayName"
DISPLAY_NAME_FIELD = f"metadata.annotations[{DISPLAY_NAME}]"
STOPPED = "status.printableStatus=Stopped"
VM_PATH = "v1/harvester/kubevirt.io.virtualmachines"
K8S_VM_PATH = "apis/kubevirt.io/v1/namespaces/{ns}/virtualmachines"
NAMESPACE_PATH = "v1/harvester/namespaces"
GROUP_LABEL = "harvester.test.io/ssp-group"
GROUP_LABEL_FIELD = f"metadata.labels[{GROUP_LABEL}]"
CONTAINER_DISK = "registry.suse.com/harvester-beta/vmi-fedora:latest"

# the namespaces the support bundle collects by default, see DefaultNamespaces() in harvester
SUPPORT_BUNDLE_NAMESPACES = {
    "cattle-dashboards", "cattle-fleet-local-system", "cattle-fleet-system",
    "cattle-fleet-clusters-system", "cattle-monitoring-system", "fleet-local",
    "harvester-system", "local", "longhorn-system", "cattle-logging-system",
    "cattle-provisioning-capi-system",
}

# name -> display name, the display names sort differently than the names
VMS = {
    "vm-a": "Web 2",
    "vm-b": "DB 1",
    "vm-c": "Web 1",
    "vm-d": "Web Server",
    "vm-e": "DB 2",
}


def list_vms(api_client, namespace, **params):
    return api_client.get_json(f"{VM_PATH}/{namespace}", **params)


def ids(data):
    return [item["id"] for item in data["data"]]


def k8s_ids(api_client, path):
    code, data = api_client.get_json(path)
    assert 200 == code, (code, data)
    return sorted(
        "/".join(filter(None, (item["metadata"].get("namespace"), item["metadata"]["name"])))
        for item in data["items"])


def k8s_vms(api_client, namespace):
    code, data = api_client.get_json(K8S_VM_PATH.format(ns=namespace))
    assert 200 == code, (code, data)
    return data["items"]


def by_display_name(vms, reverse=False):
    return sorted(vms, key=vms.get, reverse=reverse)


@pytest.fixture(scope="module")
def vm_namespace(api_client, unique_name):
    name = f"ssp-{unique_name}"[:40]
    code, data = api_client.namespaces.create(name)
    assert 201 == code, (code, data)

    yield name

    # teardown
    api_client.namespaces.delete(name)


@pytest.fixture(scope="module")
def wait_for(wait_timeout, sleep_timeout):
    def _wait_for(subject, check):
        endtime = datetime.now() + timedelta(seconds=wait_timeout)
        while endtime > datetime.now():
            result = check()
            if result:
                return result
            sleep(sleep_timeout)
        raise AssertionError(f"Timeout while waiting for {subject}")
    return _wait_for


def create_vm(api_client, name, namespace, shown_as=None):
    spec = api_client.vms.Spec(1, 1)
    spec.run_strategy = "Halted"
    spec.mgmt_network = False
    spec.add_container("disk-0", CONTAINER_DISK)
    code, data = api_client.vms.create(name, spec, namespace)
    assert 201 == code, (code, data)

    if shown_as is not None:
        set_display_name(api_client, name, namespace, shown_as)


def set_display_name(api_client, name, namespace, value):
    for _ in range(5):
        code, vm = api_client.vms.get(name, namespace)
        assert 200 == code, (code, vm)
        annotations = vm["metadata"].setdefault("annotations", {})
        annotations[DISPLAY_NAME] = value
        code, data = api_client.vms.update(name, vm, namespace)
        if code != 409:
            assert 200 == code, (code, data)
            return
        sleep(1)
    raise AssertionError(f"Cannot update {namespace}/{name}: {code}, {data}")


def delete_vm_and_wait(api_client, wait_for, name, namespace):
    code, data = api_client.vms.delete(name, namespace)
    assert code in (200, 404), (code, data)

    def gone():
        code, data = list_vms(api_client, namespace)
        return code == 200 and f"{namespace}/{name}" not in ids(data)

    wait_for(f"{name} to leave the list", gone)


@pytest.fixture(scope="module")
def vms(api_client, vm_namespace, wait_for):
    try:
        for name, shown_as in VMS.items():
            create_vm(api_client, name, vm_namespace, shown_as)

        shown = {f"{vm_namespace}/{name}": shown_as for name, shown_as in VMS.items()}

        # the list is ready when the cache has the status and the display name of every VM
        def all_indexed():
            code, data = list_vms(
                api_client, vm_namespace, filter=STOPPED, sort=DISPLAY_NAME_FIELD)
            return code == 200 and ids(data) == by_display_name(shown)

        wait_for("the VMs in the list with their status and display name", all_indexed)
        yield shown
    finally:
        for name in VMS:
            api_client.vms.delete(name, vm_namespace)


@pytest.mark.p1
@pytest.mark.virtualmachines
class TestVMListQueries:
    """ The expectations come from the Kubernetes API, not from fixed lists. """

    def test_list_matches_kubernetes(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace)
        assert 200 == code, (code, data)
        expected = sorted(f"{vm['metadata']['namespace']}/{vm['metadata']['name']}"
                          for vm in k8s_vms(api_client, vm_namespace))
        assert expected == sorted(ids(data))

    def test_other_namespace_has_no_test_vm(self, api_client, vms):
        code, data = list_vms(api_client, "default")
        assert 200 == code, (code, data)
        assert not set(vms) & set(ids(data))

    def test_projectsornamespaces(self, api_client, vm_namespace, vms):
        code, data = api_client.get_json(VM_PATH, projectsornamespaces=vm_namespace)
        assert 200 == code, (code, data)
        assert sorted(vms) == sorted(ids(data))

    def test_filter_by_exact_name(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter="metadata.name=vm-a")
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/vm-a"] == ids(data)

    def test_name_equals_is_exact_and_tilde_is_partial(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter="metadata.name=vm-")
        assert 200 == code, (code, data)
        assert [] == ids(data)

        code, data = list_vms(api_client, vm_namespace, filter="metadata.name~vm-")
        assert 200 == code, (code, data)
        assert sorted(vms) == sorted(ids(data))

    @pytest.mark.parametrize("order, reverse", [("", False), ("-", True)])
    def test_sort_by_name(self, api_client, vm_namespace, vms, order, reverse):
        code, data = list_vms(api_client, vm_namespace, sort=f"{order}metadata.name")
        assert 200 == code, (code, data)
        assert sorted(vms, reverse=reverse) == ids(data)

    @pytest.mark.parametrize("order, reverse", [("", False), ("-", True)])
    def test_sort_by_display_name(self, api_client, vm_namespace, vms, order, reverse):
        code, data = list_vms(api_client, vm_namespace, sort=f"{order}{DISPLAY_NAME_FIELD}")
        assert 200 == code, (code, data)
        assert by_display_name(vms, reverse) == ids(data)

    def test_sort_by_status_then_by_name(self, api_client, vm_namespace, vms):
        code, data = list_vms(
            api_client, vm_namespace, sort="status.printableStatus,-metadata.name")
        assert 200 == code, (code, data)
        assert sorted(vms, reverse=True) == ids(data), "all VMs have the same status"

    def test_pages_of_a_sorted_list(self, api_client, vm_namespace, vms):
        expected = sorted(vms)
        collected = []
        for page, size in ((1, 2), (2, 2), (3, 2)):
            code, data = list_vms(api_client, vm_namespace,
                                  sort="metadata.name", page=page, pagesize=size)
            assert 200 == code, (code, data)
            assert len(expected) == data["count"], "count is the total, not the page size"
            assert "pages" not in data, data
            collected.extend(ids(data))
        assert expected == collected

    def test_continue_of_a_page_is_ignored(self, api_client, vm_namespace, vms):
        code, first = list_vms(api_client, vm_namespace, sort="metadata.name", pagesize=2)
        assert 200 == code, (code, first)
        assert first.get("continue"), first

        code, data = list_vms(api_client, vm_namespace, sort="metadata.name", pagesize=2,
                              **{"continue": first["continue"]})
        assert 200 == code, (code, data)
        assert ids(first) == ids(data)

    def test_pages_beyond_the_end(self, api_client, vm_namespace, vms):
        code, data = list_vms(
            api_client, vm_namespace, sort="metadata.name", page=4, pagesize=2)
        assert 200 == code, (code, data)
        assert [] == ids(data)
        assert len(vms) == data["count"]

        code, data = list_vms(
            api_client, vm_namespace, sort="metadata.name", page=1, pagesize=50)
        assert 200 == code, (code, data)
        assert sorted(vms) == ids(data)
        assert len(vms) == data["count"]

    def test_filter_by_status(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter=STOPPED)
        assert 200 == code, (code, data)
        assert sorted(vms) == sorted(ids(data))

        code, data = list_vms(api_client, vm_namespace, filter="status.printableStatus=Running")
        assert 200 == code, (code, data)
        assert [] == ids(data)

    def test_filter_by_display_name_partial(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}~Web")
        assert 200 == code, (code, data)
        expected = sorted(vm_id for vm_id, shown_as in vms.items() if "Web" in shown_as)
        assert expected == sorted(ids(data))

    def test_partial_match_ignores_the_case(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}~web")
        assert 200 == code, (code, data)
        expected = sorted(vm_id for vm_id, shown_as in vms.items() if "Web" in shown_as)
        assert expected == sorted(ids(data))

    def test_filter_by_display_name_exact(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, filter=f'{DISPLAY_NAME_FIELD}="Web 1"')
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/vm-c"] == ids(data)

    def test_filter_value_with_space_has_to_be_quoted(self, api_client, vm_namespace, vms):
        code, data = list_vms(
            api_client, vm_namespace, filter=f'{DISPLAY_NAME_FIELD}~"Web Server"')
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/vm-d"] == ids(data)

        with api_client.override_retries(total=0):
            code, data = list_vms(
                api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}~Web Server")
        assert code >= 400, (code, data)

    def test_comma_is_or(self, api_client, vm_namespace, vms):
        code, data = list_vms(
            api_client, vm_namespace,
            filter="metadata.name=vm-a,metadata.name=vm-b", sort="metadata.name")
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/vm-a", f"{vm_namespace}/vm-b"] == ids(data)

    def test_several_filters_are_and(self, api_client, vm_namespace, vms):
        code, data = list_vms(
            api_client, vm_namespace,
            filter=[f"{DISPLAY_NAME_FIELD}~Web", f"{DISPLAY_NAME_FIELD}~1"])
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/vm-c"] == ids(data)

    @pytest.mark.parametrize("query, names", [
        ("metadata.name!=vm-a", ["vm-b", "vm-c", "vm-d", "vm-e"]),
        ("metadata.name in (vm-a,vm-c)", ["vm-a", "vm-c"]),
        ("metadata.name notin (vm-a,vm-c)", ["vm-b", "vm-d", "vm-e"]),
    ], ids=["not-equal", "in", "notin"])
    def test_filter_operators(self, api_client, vm_namespace, vms, query, names):
        code, data = list_vms(api_client, vm_namespace, filter=query, sort="metadata.name")
        assert 200 == code, (code, data)
        assert [f"{vm_namespace}/{name}" for name in names] == ids(data)

    def test_not_indexed_field_is_rejected(self, api_client, vm_namespace, vms):
        code, data = list_vms(api_client, vm_namespace, sort="spec.runStrategy")
        assert 422 == code, (code, data)

        code, data = list_vms(api_client, vm_namespace, filter="spec.runStrategy=Halted")
        assert 422 == code, (code, data)

    def test_selectors_limit_and_continue_are_ignored(self, api_client, vm_namespace, vms):
        for params in (dict(labelSelector="no-such-label=no-such-value"),
                       dict(fieldSelector="metadata.name=no-such-vm"),
                       dict(limit=1),
                       dict(limit=1, **{"continue": "not-a-token"})):
            code, data = list_vms(api_client, vm_namespace, sort="metadata.name", **params)
            assert 200 == code, (params, code, data)
            assert sorted(vms) == ids(data), params

    def test_value_that_looks_like_sql_is_harmless(self, api_client, vm_namespace, vms):
        with api_client.override_retries(total=0):
            code, data = list_vms(
                api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}~x';DROP")
        assert 200 == code, (code, data)
        assert [] == ids(data)

        code, data = list_vms(api_client, vm_namespace)
        assert 200 == code, (code, data)
        assert sorted(vms) == sorted(ids(data))

    def test_wildcards_of_a_partial_match_are_literal(
        self, api_client, vm_namespace, vms, wait_for
    ):
        shown = {"vm-wild-1": "100%", "vm-wild-2": "1000", "vm-wild-3": "a_c", "vm-wild-4": "abc"}
        try:
            for name, shown_as in shown.items():
                create_vm(api_client, name, vm_namespace, shown_as)

            def indexed():
                # the display name of the last VM is set last
                code, data = list_vms(
                    api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}=abc")
                return code == 200 and [f"{vm_namespace}/vm-wild-4"] == ids(data)

            wait_for("the VMs with the display names in the list", indexed)

            for pattern, expected in (("100%", "vm-wild-1"), ("a_c", "vm-wild-3")):
                code, data = list_vms(
                    api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}~{pattern}")
                assert 200 == code, (code, data)
                assert [f"{vm_namespace}/{expected}"] == ids(data), pattern
        finally:
            for name in shown:
                delete_vm_and_wait(api_client, wait_for, name, vm_namespace)

    def test_display_name_change_is_found(self, api_client, vm_namespace, vms, wait_for):
        set_display_name(api_client, "vm-e", vm_namespace, "Renamed")
        try:
            def found():
                code, data = list_vms(
                    api_client, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}=Renamed")
                return code == 200 and [f"{vm_namespace}/vm-e"] == ids(data)

            wait_for("the new display name in the list", found)

            code, data = list_vms(api_client, vm_namespace, filter=f'{DISPLAY_NAME_FIELD}="DB 2"')
            assert 200 == code, (code, data)
            assert [] == ids(data)
        finally:
            set_display_name(api_client, "vm-e", vm_namespace, vms[f"{vm_namespace}/vm-e"])

    def test_new_vm_is_listed_and_deleted_vm_is_gone(
        self, api_client, vm_namespace, vms, wait_for
    ):
        vm_id = f"{vm_namespace}/vm-extra"
        create_vm(api_client, "vm-extra", vm_namespace)

        def listed():
            code, data = list_vms(api_client, vm_namespace)
            return code == 200 and vm_id in ids(data)

        try:
            wait_for("the new VM in the list", listed)
        finally:
            delete_vm_and_wait(api_client, wait_for, "vm-extra", vm_namespace)

    def test_status_change_is_indexed(self, api_client, vm_namespace, vms, wait_for):
        name, vm_id = "vm-run", f"{vm_namespace}/vm-run"
        create_vm(api_client, name, vm_namespace)

        def in_status_list(stopped):
            code, data = list_vms(api_client, vm_namespace, filter=STOPPED)
            return code == 200 and (vm_id in ids(data)) == stopped

        try:
            wait_for("the new VM with the status Stopped", lambda: in_status_list(True))

            code, data = api_client.vms.start(name, vm_namespace)
            assert 204 == code or 200 == code, (code, data)
            wait_for("the started VM to leave the status Stopped", lambda: in_status_list(False))
            assert "Stopped" != k8s_status(api_client, name, vm_namespace)

            code, data = api_client.vms.stop(name, vm_namespace)
            assert 204 == code or 200 == code, (code, data)
            wait_for("the stopped VM to have the status Stopped", lambda: in_status_list(True))
        finally:
            delete_vm_and_wait(api_client, wait_for, name, vm_namespace)


def k8s_status(api_client, name, namespace):
    code, data = api_client.get_json(f"{K8S_VM_PATH.format(ns=namespace)}/{name}")
    assert 200 == code, (code, data)
    return data.get("status", {}).get("printableStatus")


@pytest.fixture(scope="module")
def namespaces(api_client, unique_name, wait_for):
    """ Three namespaces with the label group a, a, b. """
    prefix = f"ssp-ns-{unique_name}"[:30]
    groups = {f"{prefix}-1": "a", f"{prefix}-2": "a", f"{prefix}-3": "b"}
    try:
        for name, group in groups.items():
            code, data = api_client.namespaces.create(name, labels={GROUP_LABEL: group})
            assert 201 == code, (code, data)

        def all_listed():
            code, data = api_client.get_json(NAMESPACE_PATH, filter=f"metadata.name~{prefix}")
            return code == 200 and len(data["data"]) == len(groups)

        wait_for("the namespaces in the list", all_listed)
        yield prefix, groups
    finally:
        for name in groups:
            api_client.namespaces.delete(name)


@pytest.mark.p1
@pytest.mark.namespaces
class TestNamespaceListQueries:
    def test_list_has_the_namespaces(self, api_client, namespaces):
        _, groups = namespaces
        code, data = api_client.get_json(NAMESPACE_PATH)
        assert 200 == code, (code, data)
        assert set(groups) <= set(ids(data))
        assert {"default", "harvester-system"} <= set(ids(data))

    def test_filter_by_label(self, api_client, namespaces):
        prefix, groups = namespaces
        for group in ("a", "b"):
            code, data = api_client.get_json(
                NAMESPACE_PATH, filter=f"{GROUP_LABEL_FIELD}={group}", sort="metadata.name")
            assert 200 == code, (code, data)
            assert sorted(n for n, g in groups.items() if g == group) == ids(data)

    def test_filter_by_label_with_in(self, api_client, namespaces):
        _, groups = namespaces
        code, data = api_client.get_json(
            NAMESPACE_PATH, filter=f"{GROUP_LABEL_FIELD} in (a,b)", sort="metadata.name")
        assert 200 == code, (code, data)
        assert sorted(groups) == ids(data)

    def test_filter_by_label_existence(self, api_client, namespaces):
        prefix, groups = namespaces
        code, data = api_client.get_json(
            NAMESPACE_PATH, filter=[GROUP_LABEL_FIELD, f"metadata.name~{prefix}"],
            sort="metadata.name")
        assert 200 == code, (code, data)
        assert sorted(groups) == ids(data)

        code, data = api_client.get_json(
            NAMESPACE_PATH, filter=[f"!{GROUP_LABEL_FIELD}", f"metadata.name~{prefix}"])
        assert 200 == code, (code, data)
        assert [] == ids(data)

    @pytest.mark.parametrize("order, reverse", [("", False), ("-", True)])
    def test_sort_by_name(self, api_client, namespaces, order, reverse):
        prefix, groups = namespaces
        code, data = api_client.get_json(
            NAMESPACE_PATH, filter=f"metadata.name~{prefix}", sort=f"{order}metadata.name")
        assert 200 == code, (code, data)
        assert sorted(groups, reverse=reverse) == ids(data)

    def test_pages_have_the_total_count(self, api_client, namespaces):
        prefix, groups = namespaces
        collected = []
        for page in (1, 2):
            code, data = api_client.get_json(
                NAMESPACE_PATH, filter=f"metadata.name~{prefix}",
                sort="metadata.name", pagesize=2, page=page)
            assert 200 == code, (code, data)
            assert len(groups) == data["count"]
            collected.extend(ids(data))
        assert sorted(groups) == collected

    def test_projectsornamespaces(self, api_client, namespaces):
        _, groups = namespaces
        wanted = sorted(groups)[:2]
        code, data = api_client.get_json(
            NAMESPACE_PATH, projectsornamespaces=",".join(wanted), sort="metadata.name")
        assert 200 == code, (code, data)
        assert wanted == ids(data)

    def test_underscore_of_a_partial_match_is_literal(self, api_client, namespaces, wait_for):
        prefix, groups = namespaces
        names = sorted(groups)

        def set_groups(values):
            for name, group in zip(names, values):
                code, data = api_client.namespaces.update(name, dict(labels={GROUP_LABEL: group}))
                assert 200 == code, (code, data)

        set_groups(["ab_cd", "abxcd"])
        try:
            def found():
                code, data = api_client.get_json(
                    NAMESPACE_PATH,
                    filter=[f"{GROUP_LABEL_FIELD}~ab_cd", f"metadata.name~{prefix}"])
                return code == 200 and [names[0]] == ids(data)

            wait_for("the changed label in the list", found)
        finally:
            set_groups([groups[name] for name in names])

    def test_support_bundle_link_has_the_default_namespaces(self, api_client, namespaces):
        _, groups = namespaces
        code, data = api_client.get_json(NAMESPACE_PATH, link="supportbundle")
        assert 200 == code, (code, data)
        listed = ids(data)
        assert set(listed) <= SUPPORT_BUNDLE_NAMESPACES, listed
        assert {"harvester-system", "longhorn-system"} <= set(listed)
        assert len(listed) == data["count"]
        assert not set(groups) & set(listed)


UPDATED_LABEL = "harvester.test.io/ssp-updated"


@pytest.mark.p1
@pytest.mark.namespaces
class TestNamespaceCRUD:
    """ The namespace store wraps the default store, create, update and delete have to work. """

    @pytest.fixture(scope="class")
    def namespace(self, api_client, unique_name):
        name = f"ssp-crud-{unique_name}"[:40]
        yield name

        # teardown
        api_client.namespaces.delete(name)

    def listed(self, api_client, name):
        code, data = api_client.get_json(NAMESPACE_PATH, filter=f"metadata.name={name}")
        assert 200 == code, (code, data)
        return name in ids(data)

    def test_create(self, api_client, namespace):
        code, data = api_client.namespaces.create(namespace, labels={GROUP_LABEL: "crud"})
        assert 201 == code, (code, data)

        code, data = api_client.get_json(f"api/v1/namespaces/{namespace}")
        assert 200 == code, (code, data)
        assert "crud" == data["metadata"]["labels"][GROUP_LABEL]

    def test_found_by_id_and_in_the_list(self, api_client, namespace, wait_for):
        def by_id():
            code, data = api_client.namespaces.get(namespace)
            return code == 200 and namespace == data["id"]

        wait_for("the namespace by its id", by_id)
        wait_for("the namespace in the list", lambda: self.listed(api_client, namespace))

    def test_unknown_namespace_is_not_found(self, api_client, namespace):
        code, data = api_client.namespaces.get(f"{namespace}-unknown")
        assert 404 == code, (code, data)

    def test_update_labels(self, api_client, namespace, wait_for):
        for _ in range(5):
            code, data = api_client.namespaces.update(
                namespace, dict(labels={UPDATED_LABEL: "true"}))
            if code != 409:
                break
            sleep(1)
        assert 200 == code, (code, data)

        code, data = api_client.get_json(f"api/v1/namespaces/{namespace}")
        assert 200 == code, (code, data)
        assert "true" == data["metadata"]["labels"][UPDATED_LABEL]

        def by_id():
            code, data = api_client.namespaces.get(namespace)
            return code == 200 and data["metadata"]["labels"].get(UPDATED_LABEL) == "true"

        wait_for("the new label by the id of the namespace", by_id)

    def test_delete(self, api_client, namespace, wait_for):
        code, data = api_client.namespaces.delete(namespace)
        assert 200 == code, (code, data)

        def gone():
            code, _ = api_client.get_json(f"api/v1/namespaces/{namespace}")
            return 404 == code

        wait_for("the namespace to be gone", gone)
        wait_for("the namespace to leave the list",
                 lambda: not self.listed(api_client, namespace))


CONFIGMAP_PATH = "v1/harvester/configmaps"


@pytest.fixture(scope="module")
def config_maps(api_client, unique_name, wait_for):
    """ Config maps in the groups a, a, b and without a group. """
    namespace = f"ssp-lookup-{unique_name}"[:40]
    groups = {"cm-a1": "a", "cm-a2": "a", "cm-b1": "b", "cm-none": None}
    code, data = api_client.namespaces.create(namespace)
    assert 201 == code, (code, data)
    try:
        for name, group in groups.items():
            metadata = dict(name=name, namespace=namespace)
            if group:
                metadata["labels"] = {GROUP_LABEL: group}
            resp = api_client._post(
                f"api/v1/namespaces/{namespace}/configmaps",
                json=dict(apiVersion="v1", kind="ConfigMap", metadata=metadata))
            assert 201 == resp.status_code, resp.text

        def all_listed():
            code, data = api_client.get_json(f"{CONFIGMAP_PATH}/{namespace}")
            return code == 200 and set(f"{namespace}/{n}" for n in groups) <= set(ids(data))

        wait_for("the config maps in the list", all_listed)
        yield namespace
    finally:
        api_client.namespaces.delete(namespace)


@pytest.mark.p1
@pytest.mark.namespaces
class TestLookupQueries:
    """ The queries the UI uses to look up objects: a filter on a label and a filter with in. """

    def names(self, api_client, namespace, filter):
        code, data = api_client.get_json(
            f"{CONFIGMAP_PATH}/{namespace}", filter=filter, sort="metadata.name")
        assert 200 == code, (code, data)
        return [i.split("/", 1)[1] for i in ids(data)]

    def test_filter_by_the_value_of_a_label(self, api_client, config_maps):
        assert ["cm-a1", "cm-a2"] == self.names(
            api_client, config_maps, f"{GROUP_LABEL_FIELD}=a")
        assert ["cm-b1"] == self.names(api_client, config_maps, f"{GROUP_LABEL_FIELD}=b")

    def test_filter_by_a_label_with_in(self, api_client, config_maps):
        assert ["cm-a1", "cm-a2", "cm-b1"] == self.names(
            api_client, config_maps, f"{GROUP_LABEL_FIELD} in (a,b)")

    def test_filter_by_the_name_with_in(self, api_client, config_maps):
        assert ["cm-a1", "cm-none"] == self.names(
            api_client, config_maps, "metadata.name in (cm-a1,cm-none)")

    def test_filter_a_cluster_scoped_resource_by_the_name_with_in(self, api_client):
        code, data = api_client.get_json(
            NAMESPACE_PATH, filter="metadata.name in (harvester-system,longhorn-system)",
            sort="metadata.name")
        assert 200 == code, (code, data)
        assert ["harvester-system", "longhorn-system"] == ids(data)


# the types the UI lists, a type that the cluster does not have is skipped
LIST_TYPES = [
    "node",
    "namespace",
    "persistentvolumeclaim",
    "secret",
    "configmap",
    "event",
    "pod",
    "storage.k8s.io.storageclass",
    "kubevirt.io.virtualmachineinstance",
    "k8s.cni.cncf.io.network-attachment-definition",
    "harvesterhci.io.virtualmachineimage",
    "harvesterhci.io.virtualmachinetemplate",
    "harvesterhci.io.virtualmachinetemplateversion",
    "harvesterhci.io.keypair",
    "harvesterhci.io.setting",
    "harvesterhci.io.addon",
    "devices.harvesterhci.io.pcidevice",
    "devices.harvesterhci.io.usbdevice",
    "devices.harvesterhci.io.usbdeviceclaim",
    "devices.harvesterhci.io.sriovgpudevice",
    "devices.harvesterhci.io.vgpudevice",
    "devices.harvesterhci.io.sriovnetworkdevice",
]
# the objects of these types do not come and go while the tests run
STABLE_TYPES = {
    "node", "storage.k8s.io.storageclass", "harvesterhci.io.setting", "harvesterhci.io.addon",
    "devices.harvesterhci.io.pcidevice", "devices.harvesterhci.io.usbdevice",
    "devices.harvesterhci.io.sriovgpudevice", "devices.harvesterhci.io.vgpudevice",
    "devices.harvesterhci.io.sriovnetworkdevice",
}


@pytest.mark.p1
@pytest.mark.virtualmachines
class TestListOtherTypes:
    """ The SQL cache serves every list of /v1/harvester, not only the lists of VMs. """

    @pytest.mark.parametrize("type_id", LIST_TYPES)
    def test_list(self, api_client, type_id):
        code, schema = api_client.get_json(f"v1/harvester/schemas/{type_id}")
        if code == 404:
            pytest.skip(f"The cluster has no type {type_id}")
        assert 200 == code, (code, schema)
        assert "GET" in schema["collectionMethods"], schema

        collection = urlparse(schema["links"]["collection"]).path
        code, data = api_client.get_json(collection)
        assert 200 == code, (code, data)
        assert "data" in data, data
        if "count" in data:
            assert len(data["data"]) == data["count"]

        if type_id in STABLE_TYPES:
            attributes = schema["attributes"]
            group = attributes.get("group")
            prefix = f"apis/{group}" if group else "api"
            path = f"{prefix}/{attributes['version']}/{attributes['resource']}"
            expected = k8s_ids(api_client, path)
            assert expected == sorted(ids(data))

    def test_list_with_sort_and_page(self, api_client):
        code, data = api_client.get_json(
            "v1/harvester/nodes", sort="-metadata.name", pagesize=1, page=1)
        assert 200 == code, (code, data)
        assert 1 == len(data["data"])
        assert data["count"] >= 1


def apiserver_pods(api_client):
    code, data = api_client.get_json(
        "api/v1/namespaces/harvester-system/pods",
        labelSelector="app.kubernetes.io/name=harvester,app.kubernetes.io/component=apiserver")
    assert 200 == code, (code, data)
    return sorted(pod["metadata"]["name"] for pod in data["items"]
                  if pod["status"].get("phase") == "Running"
                  and not pod["metadata"].get("deletionTimestamp"))


def list_vms_of_pod(api_client, pod, namespace, **params):
    """ The API server of a single replica, through the Kubernetes API proxy for pods. """
    proxy = f"api/v1/namespaces/harvester-system/pods/https:{pod}:8443/proxy"
    return api_client.get_json(f"{proxy}/{VM_PATH}/{namespace}", **params)


@pytest.mark.p2
@pytest.mark.virtualmachines
class TestAPIServerReplicas:
    """ Every replica of the API server has its own cache. """

    def test_every_replica_lists_the_same(self, api_client, vm_namespace, vms):
        pods = apiserver_pods(api_client)
        assert pods, "no running pod of the API server"
        for pod in pods:
            code, data = list_vms_of_pod(api_client, pod, vm_namespace, sort="metadata.name")
            assert 200 == code, (pod, code, data)
            assert sorted(vms) == ids(data), pod

    def test_every_replica_sees_a_change(self, api_client, vm_namespace, vms, wait_for):
        pods = apiserver_pods(api_client)
        set_display_name(api_client, "vm-e", vm_namespace, "Replicated")
        try:
            for pod in pods:
                def found():
                    code, data = list_vms_of_pod(
                        api_client, pod, vm_namespace, filter=f"{DISPLAY_NAME_FIELD}=Replicated")
                    return code == 200 and [f"{vm_namespace}/vm-e"] == ids(data)

                wait_for(f"the change in the list of {pod}", found)
        finally:
            set_display_name(api_client, "vm-e", vm_namespace, vms[f"{vm_namespace}/vm-e"])

    def test_list_after_the_restart_of_a_replica(self, api_client, vm_namespace, vms, wait_for):
        """ The new pod starts with an empty cache, the first request fills it. """
        before = apiserver_pods(api_client)
        assert before, "no running pod of the API server"
        victim = before[0]

        code, data = api_client.delete_json(f"api/v1/namespaces/harvester-system/pods/{victim}")
        assert code in (200, 202), (code, data)

        def replaced():
            # the API is not available while the only replica restarts
            try:
                with api_client.override_retries(total=0):
                    now = apiserver_pods(api_client)
            except (AssertionError, requests.exceptions.RequestException):
                return None
            return [pod for pod in now if pod not in before] if len(now) == len(before) else None

        new_pods = wait_for("the new pod of the API server", replaced)

        def listed():
            try:
                with api_client.override_retries(total=0):
                    code, data = list_vms_of_pod(
                        api_client, new_pods[0], vm_namespace, sort="metadata.name")
            except requests.exceptions.RequestException:
                return False
            return code == 200 and sorted(vms) == ids(data)

        wait_for(f"the list of {new_pods[0]}", listed)

        code, data = list_vms(api_client, vm_namespace, sort="metadata.name")
        assert 200 == code, (code, data)
        assert sorted(vms) == ids(data)


def open_subscription(api_client, resource_type, **options):
    websocket = pytest.importorskip("websocket", reason="needs the websocket-client package")

    endpoint = urlparse(api_client.endpoint)
    host = endpoint.netloc
    ws = websocket.create_connection(
        f"wss://{host}/v1/harvester/subscribe",
        header=[f"Authorization: {api_client.session.headers['Authorization']}"],
        origin=f"https://{host}",
        sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
        timeout=10,
    )
    ws.send(json.dumps(dict(resourceType=resource_type, **options)))
    return ws


@pytest.mark.p1
@pytest.mark.virtualmachines
class TestVMWatch:
    """ The events of the VMs of the test, other events are skipped. """

    def next_event(self, ws, match, timeout=30):
        websocket = pytest.importorskip("websocket")
        endtime = datetime.now() + timedelta(seconds=timeout)
        seen = []
        ws.settimeout(5)
        while endtime > datetime.now():
            try:
                message = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:
                continue
            except ValueError:
                continue
            name = message.get("name")
            obj_id = (message.get("data") or {}).get("id")
            if match(name, obj_id):
                return message
            seen.append(f"{name} {obj_id}")
        raise AssertionError(f"Timeout while waiting for an event, skipped events: {seen}")

    def test_existing_vms_are_not_replayed(self, api_client, vm_namespace, vms):
        """ A watch without resourceVersion only sends the changes after the subscription. """
        websocket = pytest.importorskip("websocket")
        code, data = list_vms(api_client, vm_namespace)
        assert 200 == code, (code, data)

        ws = open_subscription(api_client, "kubevirt.io.virtualmachine")
        try:
            self.next_event(ws, lambda name, _: name == "resource.start")

            replayed = []
            endtime = datetime.now() + timedelta(seconds=8)
            ws.settimeout(2)
            while endtime > datetime.now():
                try:
                    message = json.loads(ws.recv())
                except websocket.WebSocketTimeoutException:
                    continue
                except ValueError:
                    continue
                obj_id = (message.get("data") or {}).get("id")
                if message.get("name") == "resource.create" and obj_id in vms:
                    replayed.append(obj_id)
            assert [] == replayed
        finally:
            ws.close()

    def test_create_change_remove(self, api_client, vm_namespace, vms, wait_for):
        vm_id = f"{vm_namespace}/vm-watch"
        # list once, so the cache of the type exists before the watch starts
        code, data = list_vms(api_client, vm_namespace)
        assert 200 == code, (code, data)

        ws = open_subscription(api_client, "kubevirt.io.virtualmachine")
        try:
            self.next_event(ws, lambda name, _: name == "resource.start")

            create_vm(api_client, "vm-watch", vm_namespace)
            self.next_event(
                ws, lambda name, obj_id: name == "resource.create" and obj_id == vm_id)

            set_display_name(api_client, "vm-watch", vm_namespace, "Changed")

            def changed(name, obj_id):
                return name == "resource.change" and obj_id == vm_id
            while True:
                event = self.next_event(ws, changed)
                annotations = event["data"]["metadata"].get("annotations", {})
                if annotations.get(DISPLAY_NAME) == "Changed":
                    break

            def deleted():
                code, data = api_client.vms.delete("vm-watch", vm_namespace)
                assert code in (200, 404), (code, data)
                return code == 200

            wait_for("the delete of the new VM", deleted)
            self.next_event(
                ws, lambda name, obj_id: name == "resource.remove" and obj_id == vm_id)
        finally:
            ws.close()
            api_client.vms.delete("vm-watch", vm_namespace)

    def test_changes_mode_notifies_about_a_new_vm(self, api_client, vm_namespace, vms):
        websocket = pytest.importorskip("websocket")
        code, data = list_vms(api_client, vm_namespace)
        assert 200 == code, (code, data)

        ws = open_subscription(
            api_client, "kubevirt.io.virtualmachine", mode="resource.changes", debounceMs=100)
        try:
            self.next_event(ws, lambda name, _: name == "resource.start")

            # wait until nothing arrives anymore, so the notification is for the new VM
            ws.settimeout(0.5)
            while True:
                try:
                    ws.recv()
                except websocket.WebSocketTimeoutException:
                    break

            create_vm(api_client, "vm-notify", vm_namespace)
            self.next_event(ws, lambda name, _: name == "resource.changes")
        finally:
            ws.close()
            api_client.vms.delete("vm-notify", vm_namespace)
