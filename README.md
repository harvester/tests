# About 

This is a harvester test framework which uses python pytest library. This framework heavily depends on the pytest fixtures which are defined in conftest.py

## Pre-requisites

Before running these tests, bring up a virtual harvester environment following the instructions in repo https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester

In addition, the tests are executed via [tox][tox] so make sure it is installed,
either via [Python pip][pip] or vendor package manager.

## Pytest Fixtures

They help us set up some helper code that should run before any tests are executed, and are perfect for setting-up resources that are needed by the tests. They are defined in conftest.py under the apis folder.

These fixture are executed at the session level and they are used to provide the authentication and to get the api endpoints before executing tests for a particular api

## Running Tests

Update config.yml with values for each entry based on the harvester environment the tests are run against.

### Run All Tests

To run the entire Harvester end-to-end test suite:

```console
tox -e py36 -- harvester_e2e_tests --html=test_result.html
```

### API Tests 

API Tests are designed to test REST APIs for one resource (i.e. keypairs,
vitualmachines, virtualmachineimages, etc) at a time.

Since deleting the host is irreversible process, run delete_host test after 
running all the other tests

As mentioned before, the test will be executed via the [tox][tox]
environments. Currently, both Python3.6 and Python3.8 are supported.

For example, to run the API tests in a Python3.6 environment for the first time,
and skipping the delete_host test against a freshly installed single node Harvester:
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

### Scenario Tests

Scenario tests are designed to test a specific use case or scenario at a time,
which may involved a combination of resources in an orchestrated workflow.

Like the API tests, the scenario tests are also running inside the
[tox][tox]-managed environments. Currently, both Python3.6 and Python3.8 are
supported.

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

### Adding Host Management Scripts

Some tests required manipulating the hosts where the VMs are running in order to
test scheduling resiliency and disaster recovery scenarios. Therefore, we need
external scripts to power-on, power-off, and to reboot a given node. The
host management scripts are expected to be provided by users out-of-band.
Reasons are:

1. the scripts are very specific to the Harvester environment. For example,
   for a virtual vagrant environment, the scripts may simply just performing
   `vagrant halt <node name>` and `vagrant up <node name>`. However for a
   baremetal environment managed by IPMI, the scripts may need to
   use IPMO tools CLI.
2. for certain environments (i.e. IPMI, RedFish, etc), credential is required.

The host management scripts must all be placed into the same directory and must
be named `power_on.sh`, `power_off.sh`, and `reboot.sh`. All the scripts must
accept exactly one parameter, which is the name of the host. Please see the
`scripts` directory for examples.

Host management tests must be invoked with the `host_management` marker.
For example, to run the host management tests:

```console
tox -e py38 -- -m "host_management"
```

---
**NOTE**

Must also provide the `--node-scripts-location` parameter in config.yml, which points to the
directory which contains the host management shell scripts.

---

## Running terraform tests
---------------------------

To run the tests which uses terraform to create each resource, it uses the 
scripts in scripts/terraform folder
```console
tox -e py36 -- harvester_e2e_tests/apis --html=test_result.html -m terraform
tox -e py36 -- harvester_e2e_tests/scenarios/test_vm_networking.py --html=test_result.html -m terraform
```

## Running delete Host tests
----------------------------

To run the delete_host tests at the end when all tests are done running
```console
tox -e py36 -- harvester_e2e_tests/apis --html=test_result.html -m delete_host
```

## Running Backup tests
-----------------------

To run the backup tests for both S3 and NFS endpoint, provide the S3 and nfs
endpoint either on command line or in config.yml
```console
tox -e py36 -- harvester_e2e_tests --html=test_result.html --accessKeyId <accessKey> --secretAccessKey <secretaccesskey> --bucketName <bucket> --region <region> --nfs-endpoint nfs://<IP>/<path> -m backup
```

## Running Linter
-----------------

We are using the standard [flake8][flake8] linter to enforce coding style. To
run the linter:

```console
tox -e pep8
```

## Adding New tests
--------------------

Add new api tests under the apis folder. Pytest expects tests to be located in files whose names begin with test_ or end with _test.py

Add any new fixtures in conftest.py. Fixture functions are created by marking them with the @pytest.fixture decorator. Test functions that require fixtures should accept them as arguments.

[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pip.pypa.io/en/stable/
[flake8]: https://flake8.pycqa.org/en/latest/

## Manual Test Cases
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

# Preview the website
To preview the website changes, you will need to [install Hugo](https://gohugo.io/getting-started/installing/).
Once Hugo is installed, run the following:
```shell
hugo server --buildDrafts --buildFuture
```
The site will be accessible at http://localhost:1313.

