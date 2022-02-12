# Table Of Contents

- [Overview](#overview)
     - [Prerequisites](#prerequisites)
          - [Virtual Harvester Cluster](#virtual_harvester_cluster)
          - [Networking](#networking)
          - [Host Management Scripts](#host_management_scripts)
          - [Terraform](#terraform_cli)
          - [Image Caching](#image_caching)
     - [Running Tests](#running_tests)
          - [The --do-not-cleanup option](#do_not_cleanup)
          - [Run All Tests](#run_all_tests)
          - [Run API Tests Only](#run_api_tests_only)
          - [Run Scenario Tests Only](#run_scenario_tests_only)
          - [Run Terraform Tests Only](#run_terraform_tests_only)
          - [Run Delete Host Tests Only](#run_delete_host_tests_only)
          - [Run Backup & Restore Tests Only](#run_backup_and_restore_tests_only)
          - [Run Rancher Integration Tests Only](#run_rancher_integration_tests_only)
     - [Running Linter](#running_linter)
- [Adding New Tests](#adding_new_tests)
- [Manual Test Cases](#manual_test_cases)
     - [Generating the test doc sites](#generating_docs)


# Overview <a name="overview" />

This repo contains Harvester end-to-end (e2e) test suite, implemented using Python [pytest][pytest] framework. In addition, it is also the home of all the [Harvester manual test cases][Harvester manual test cases]. The e2e test suite is a subset of [Harvester manual test cases][Harvester manual test cases], which is intended to be utilized by CI (i.e. Jenkins) to automatically test Harvester backend functionality.

## Prerequisites <a name="prerequisites" />

The (e2e) tests are expected to be ran against a given Harvester cluster. In addition, the tests are executed via [tox][tox] so make sure it is installed, either via [Python pip][pip] or vendor package manager.

Optionally, in order to run the Rancher integration tests, an external Rancher cluster is also required. The Rancher integration tests are disabled unless the Rancher (API) endpoint is specified.

To run the NFS backup & restore tests, an NFS endpoint is required. Likewise, in order to run the [AWS S3][AWS S3] backup & restore tests, S3 bucket name and access credential must be provided. The backup & restore tests are disabled unless the required NFS endpoint or S3 access parameters are specified.

### Virtual Harvester Cluster <a name="virtual_harvester_cluster" />

For test case development, we recommend using a virtual Harvester cluster as it is self-contained, disposable, and repeatable. Please refer to the instructions in https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester on how to setup a virtual Harvester cluster.

### Networking <a name="networking" />

Some tests required VLAN networking. Those tests are disabled unless a VLAN ID and VLAN interface (NIC) are specified. For those tests to be successful, the VLAN routing and DHCP must be properly setup prior to running the tests. Setting up VLAN networking is infrastructure-specific, and therefore outside the scope of this document. Please work with your IT infrastructure team create the appropriate VLANs.

When using the virtual Harvester cluster (i.e. vagrant-pxe-harvester), the VLAN ID must be `1`, and the VLAN NIC must be `harvester-mgmt`.

### Host Management Scripts <a name="host_management_scripts" />

Some tests required manipulating the hosts where the VMs are running in order to
test scheduling resiliency and disaster recovery scenarios. Therefore, we need
external scripts to power-on, power-off, and to reboot a given Harvester node. The
host management scripts are expected to be provided by users out-of-band for the following reasons:

1. the scripts are specific to the Harvester environment. For example,
   for a virtual vagrant environment, the scripts may simply just performing
   `vagrant halt <node name>` and `vagrant up <node name>`. However for a
   baremetal environment managed by IPMI, the scripts may need to
   use IPMI CLI.
2. for certain environments (i.e. IPMI, RedFish, etc), credential is required.

The host management scripts must all be placed into the same directory and must
be named `power_on.sh`, `power_off.sh`, and `reboot.sh`. All the scripts must
accept exactly two parameters, which are host name and host IP. Please see the
[scripts/vagrant](scripts/vagrant) directory for examples.

Host management tests must be invoked with the `host_management` marker, along with the `--node-scripts-location` parameter which points to the directory that contains the host management shell scripts.

For example, to run the host management tests:

```console
tox -e py38 -- -m "host_management" --node-scripts-location ./scripts
```

### Terraform CLI <a name="terraform_cli" />

The Harvester [terraform][terraform] test requires [terraform][terraform] CLI. Please refer to [terraform][terraform] on how to download and install the CLI.

### Image Caching <a name="image_caching" />

While running the tests, the image fixtures will attempt to create the test images by providing the download URLs for the various cloud image providers (e.g. `htps://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.3/images/openSUSE-Leap-15.3.x86_64-NoCloud.qcow2`). Sometimes a given cloud image provider URL can be slow or inaccessible, which cause the underlying tests to fail. Therefore, it is recommended to create a local web server to cache the images that the tests depended on. We can then use the `--image-cache-url` parameter to convey the image cache URL to the tests. The absence of the `--image-cache-url` parameter means the tests will attempt to directly download the images directly from the cloud image providers instead.

## Running Tests <a name="running_tests" />

There are two types of tests, [APIs](harvester_e2e_tests/apis) and [scenarios](harvester_e2e_tests/scenarios) respectively. [APIs](harvester_e2e_tests/apis) tests are designed to test simple resource creation using backend APIs, while the [scenarios](harvester_e2e_tests/scenarios) tests are intended for testing workflows involving multiple resources.

Tests are executed in Python [tox][tox] environments. Both Python3.6 and Python 3.8 are supported.

Prior to running the (e2e) tests, you must edit [config.yml](config.yml) to provide the correct configuration. Each configuration option is self-documented. 

---
**NOTE:**

The configuration options in [config.yml](config.yml) can be overwritten by command line parameters. For example, to overwrite the `endpoint` option, we can use the `--endpoint` parameter while running the tests. 
---

### The --do-not-cleanup option <a name="do_not_cleanup" />

All the resources/artifacts created by the tests will be cleaned up upon exit. If you need to preserve them for debugging purposes, you may use the `--do-not-cleanup` parameter when running the tests. For example:

```console
tox -e py38 -- harvester_e2e_tests --html=test_result.html --do-not-cleanup
```

### Run All Tests <a name="run_all_tests" />

To run the entire test suite, all the configuration option in [config.yml](config.yml) are required.

```console
tox -e py38 -- harvester_e2e_tests --html=test_result.html
```

### Run API Tests Only <a name="run_api_tests_only" />

API Tests are designed to test REST APIs for one resource (i.e. keypairs,
vitualmachines, virtualmachineimages, etc) at a time. For example:

```console
tox -e py36 -- harvester_e2e_tests/apis --html=test_result.html
```

---
**NOTE:**

Since deleting the host is irreversible process, run `delete_host` test after running all the other tests
---

For example, to run the API tests in a Python3.6 environment for the first time,
and skipping the delete_host test:

```console
tox -e py36 -- harvester_e2e_tests/apis --html=test_result.html -m "not delete_host"
```

To run the API tests in a Python3.8 environment:
```console
tox -e py38 -- harvester_e2e_tests/apis --html=test_result.html -m "not delete_host"
```
To skip multiple marker tests, for example: delete_host, host_management, multi_node_scheduling
```console
tox -e py38 -- harvester_e2e_tests/apis --html=test_result.html -m "not delete_host and not host_management and not multi_node_scheduling"

```

Example Output:
```console
============================= test session starts ==============================
platform linux -- Python 3.6.12, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
rootdir: <Folder from where tests are running> 
plugins: metadata-1.11.0, html-3.1.1
collected 22 items                                                             

apis/test_images.py .....                                                [ 22%]
apis/test_keypairs.py .....                                              [ 45%]
apis/test_settings.py ..                                                 [ 54%]
apis/test_users.py ...                                                   [ 68%]
apis/test_vm_templates.py ...                                            [ 81%]
apis/test_volumes.py ....                                                [100%]

----------- generated html file: file:///<home Folder>/tests/test_result.html -----------
```

### Run Scenario Tests Only <a name="run_scenario_tests_only" />

Scenario tests are designed to test a specific use case or scenario at a time,
which may involved a combination of resources in an orchestrated workflow.

To run the scenario tests in a Python3.6 environment:
```console
tox -r -e py36 -- harvester_e2e_tests/scenarios --html=test_result.html
```

To skip the multi_node_scheduling tests which are run in a multi-node cluster where some
hosts have more resources than others in order to test VM scheduling behavior
```console
tox -r -e py36 -- harvester_e2e_tests/scenarios --html=test_result.html -m "not multi_node_scheduling"
```

To run just the multi_node_scheduling tests
```console
tox -r -e py36 -- harvester_e2e_tests/scenarios --html=test_result.html -m muti_node_scheduling
```

To run the scenario tests in a Python3.8 environment:
```console
tox -r -e py38 -- harvester_e2e_tests/scenarios --html=test_result.html
```
By default the tests will cleanup after themselves. If you want to preserve the
test artifact for debugging purposes, you may specific the `--do-not-cleanup`
flag. For example:
```console
tox -r -e py38 -- harvester_e2e_tests/scenarios --html=test_result.html --do-not-cleanup
```

### Run Terraform Tests Only  <a name="run_terraform_tests_only" />

To run the tests which uses terraform to create each resource, it uses the 
scripts in [terraform_test_artifacts](terraform_test_artifacts) folder. For example:


```console
tox -e py38 -- harvester_e2e_tests --html=test_result.html -m terraform
```

### Run Delete Host Tests Only <a name="run_delete_host_tests_only" />

To run the delete_host tests at the end when all tests are done running. For example:

```console
tox -e py38 -- harvester_e2e_tests/apis --html=test_result.html -m delete_host
```

### Run Backup & Restore Tests Only <a name="run_backup_and_restore_tests_only" />

To run the backup tests for both S3 and NFS endpoint, provide the S3 and nfs
endpoint either on command line or in [config.yml](config.yml).

```console
tox -e py38 -- harvester_e2e_tests --html=test_result.html --accessKeyId <accessKey> --secretAccessKey <secretaccesskey> --bucketName <bucket> --region <region> --nfs-endpoint nfs://<IP>/<path> -m "backup_and_restore_p1 and backup_and_restore_p2"
```

### Run Rancher Integration Tests Only <a name="run_rancher_integration_tests_only" />

An external Rancher instance is required in order to run Harvester Rancher integration tests. Furthermore, the external Rancher instance must be reachable by
the Harvester nodes. Conversely, the Harvester VIP must also be reachable by
Rancher during cluster provisioning. Both `--rancher-endpoint` and `--rancher-admin-password` arguments must be specified in order to run the Rancher integration tests. Optionally, user may specify `--kubernetes-version` argument to for a specific Kubernetes version to use when provisioning an RKE cluster via Harvester node driver. If `--kubernetes-version` is absent, Kubernetes version `v1.21.6+rke2r1` will be used.

To run Rancher integration tests, for example:

```console
tox -e py38 -- harvester_e2e_tests/scenarios/test_rancher_integration.py --endpoint https://192.168.0.131 --rancher-endpoint https://rancher-instance --rancher-admin-password rancher_password --kubernetes-version v1.27.1+rke2r2
```

If the external Rancher instance is shared by multiple Harvester environments, user should also provide the `--test-environment` argument to distinguish the artifacts created by the current test environment in case manual cleanup is needed. All the artifacts (e.g. RKE2 clusters, cloud credentials, import Harvester cluster, etc) have the test environment name it their names (e.g. harvester-<test environment>-<random string>). For example:

```console
tox -e py38 -- harvester_e2e_tests/scenarios/test_rancher_integration.py --endpoint https://192.168.0.131 --rancher-endpoint https://rancher-instance --rancher-admin-password rancher_password --kubernetes-version v1.27.1+rke2r2 --test-environment browns
```

## Running Linter <a name="running_linter" />

We are using the standard [flake8][flake8] linter to enforce coding style. To
run the linter:

```console
tox -e pep8
```

# Adding New Tests <a name="adding_new_tests" />

The e2e tests were implemented using the Python [pytest][pytest] framework. An e2e test case should be corresponding to one or more manual test cases [here](https://harvesterhci.io/tests/manual/). Likewise, if a manual test case is implemented by e2e, it should have the ***(e2e_be)*** designation in it's title.

[Pytest][pytest] expects tests to be located in files whose names begin with ***test_*** or end with ***_test.py***.

Here are the general guidelines for adding a new e2e test:

- If the test requires new configurations, make sure to add them to both [config.yml](config.yml) and [harvester_e2e_tests/conftest.py](harvester_e2e_tests/conftest.py). [config.yml](config.yml) should have the default values.
- Add the common [fixtures][pytest fixtures] in [harvester_e2e_tests/fixtures](harvester_e2e_tests/fixtures). If the [fixtures][pytest fixtures] is specific to a test only, it should be added to that particular test file.
- All [fixtures][pytest fixtures] must be able to cleanup itself using the [recommended yield technique](https://docs.pytest.org/en/6.2.x/fixture.html#yield-fixtures-recommended)
- All fixtures must implement the `--do-not-cleanup` option. Here's an [example](https://github.com/harvester/tests/blob/main/harvester_e2e_tests/fixtures/image.py#L42-L44).
- Add new Harvester API endpoints must be added to [harvester_e2e_tests/templates/api_endpoints.json.j2](harvester_e2e_tests/templates/api_endpoints.json.j2).
- Add new Rancher API endpoints to [harvester_e2e_tests/templates/rancher_api_endpoints.json.j2](harvester_e2e_tests/templates/rancher_api_endpoints.json.j2).
- Backend API request contents should be templatize whenever possible. We are using Python [jinja2][jinja2] for templating. Add the new API request templates should be added in [harvester_e2e_tests/templates](harvester_e2e_tests/templates).
- Add new API tests in [harvester_e2e_tests/apis](harvester_e2e_tests/apis).
- Add new scenario tests in [harvester_e2e_tests/scenarios](harvester_e2e_tests/scenarios).
- Any sharable, common helper functionalities should be added in [harvester_e2e_tests/utils.py](harvester_e2e_tests/utils.py).
- Tests should be using [fixtures][pytest fixtures] as much as possible as the [fixtures][pytest fixtures] should be able to cleanup after itself upon exit. Otherwise, the test must cleanup whatever artifacts it create upon exit.
- A test should have one or more [pytest markers][pytest markers] which corresponding to one or more [Harvester manual test cases][Harvester manual test cases]. For example, https://github.com/harvester/tests/blob/main/harvester_e2e_tests/scenarios/test_create_vm.py#L88-L112.
- Use `@pytest.mark.p1` marker if the test is a priority 1 test.
- Use `@pytest.mark.p2` marker if the test is a priority 2 test.
- New custom markers should be added in [harvester_e2e_tests/conftest.py](harvester_e2e_tests/conftest.py). For example, https://github.com/harvester/tests/blob/main/harvester_e2e_tests/conftest.py#L190
- By using markers, you can skip a test based on specified parameters. For example, you can skip S3 backup tests if access key is not provided. See https://github.com/harvester/tests/blob/main/harvester_e2e_tests/conftest.py#L339-L344.

# Manual Test Cases <a name="manual_test_cases" />

Some scenarios are hard to test using the automation tests and are documented as manual test cases that need to be verified before release.
The manual test cases are accessible [here](https://harvesterhci.io/tests/manual/).

The manual test case pages can be edited under `docs/content/manual/`.

To categorize tests, place them in sub-directories under `docs/content/manual/`.
These sub-directories must contain a file named `_index.md` with the following:
```markdown
---
title: Name of Test Category
---
Optional description regarding the test category.
```

Each test page should be structured as such:
```markdown
---
title: Name of Test Case
---
Description of the test case.
```

Both of these files can contain Markdown in the title and page body.

# Generating the test doc sites <a name="generating_docs" />

You can generate all of the test sites locally with the `Makefile`. There are a couple of pre-requisites for it to work.
- [install Hugo](https://gohugo.io/getting-started/installing/)
- install pip
- install npm

The makefile allows you to do the following
- `make all`
     - This will create all of the docs sites and put them into `docs/public/`
- `make run`
     - This will clean out all of the directories, then generate backend and frontend docs, then generate a hugo server that outputs at `/tmp/hugo/` and run a local web server that you can use to look at all of the docs locally. 
     - It will auto-regenerate any hugo manual tests, but won't update with the backend and frontend in real time. You will have to run it again.
- `make backend`
     - this will generate the docs for the Python e2e tests. They will generate at `harvester_e2e_tests/harvester_e2e_tests/`
- `make frontend`
     - This will generate the docs for the Cypress frontend e2e tests at `cypress/docs/`
- `make clean`
     - This will delete all of the static site assets in
          - `docs/public/`
          - `cypress/docs`
          - `harvester_e2e_tests/harvester_e2e_tests`


[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pip.pypa.io/en/stable/
[flake8]: https://flake8.pycqa.org/en/latest/
[jinja2]: https://jinja2docs.readthedocs.io/en/stable/
[pytest]: https://docs.pytest.org/en/6.2.x/
[pytest fixtures]: https://docs.pytest.org/en/6.2.x/fixture.html#fixture
[pytest markers]: https://docs.pytest.org/en/6.2.x/example/markers.html
[terraform]: https://www.terraform.io/
[AWS S3]: https://aws.amazon.com/s3/
[Harvester manual test cases]: https://github.com/harvester/tests/tree/main/docs/content/manual

# Test skeletons

Test skeletons are codes that needs to be checked into the code base to describe the test steps.

## Frontend test skeletons

## Backend test skeletons

Backend test is driven by pytest. Code are located at [`harvester_e2e_tests`](harvester_e2e_tests/) directory.

There are two types of tests, [APIs](harvester_e2e_tests/apis) and [scenarios](harvester_e2e_tests/scenarios) respectively. [APIs](harvester_e2e_tests/apis) tests are designed to test simple resource creation using backend APIs, while the [scenarios](harvester_e2e_tests/scenarios) tests are intended for testing workflows involving multiple resources.

Make sure to choose the proper directory and file to place the test skeleton.

A backend test skeleton looks like this:

```
@pytest.mark.skip(reason="TODO")
def test_single_replica_failed_during_engine_start():
    """
    Test if the volume still works fine when there is
    an invalid replica/backend in the engine starting phase.

    Prerequisite:
    Setting abc = true

    1. Create a pod using Longhorn volume.
    2. Write some data to the volume then get the md5sum.
    3...
    """
    pass
```

Make sure:
1. Add @pytest.mark.skip(reason="TODO") to indicate this test should be skipped due to it’s not implemented.
1. Don’t fill in the parameter (fixture) of the function.
1. Describe the test case purpose and steps well in the docstring/comment.
1. Add pass at the end of the function.
1. Don’t assume the default setting will always work. Call out the expected settings in the prerequisite and they should be set explicitly at the beginning of the test. Use the fixture client or others to reset any changed settings back to default.

