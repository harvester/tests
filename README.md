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

### Run All Tests

To run the entire Harvester end-to-end test suite:

```console
tox -e py36 -- harvester_e2e_tests --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html
```

### API Tests 

API Tests are designed to test REST APIs for one resource (i.e. keypairs,
vitualmachines, virtualmachineimages, etc) at a time.

To run all the API tests under the `harvester_e2e_tests\apis` folder, maintain
the count of harvester_cluster_nodes(1 for single node and 3 for 3-node
cluster) in config.yml. It can also be set as an option while executing the
pytest.

Since deleting the host is irreversible process, run delete_host test after 
running all the other tests

As mentioned before, the test will be executed via the [tox][tox]
environments. Currently, both Python3.6 and Python3.8 are supported.

For example, to run the tests in a Python3.6 environment for the first time,
and skipping the delete_host test against a freshly installed single node Harvester:
```console
tox -e py36 -- harvester_e2e_tests/apis --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html -m "not delete_host"
```

To pass the harverster_cluster_nodes as option:
```console
tox -e py36 -- harvester_e2e_tests/apis --endpoint https://<harvester_node_0 IP>:30443 --harvester_cluster_nodes 1 --html=test_result.html -m "not delete_host"
```

To run the API tests in a Python3.8 environment:
```console
tox -e py38 -- harvester_e2e_tests/apis --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html -m "not delete_host"
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
tox -r -e py36 -- harvester_e2e_tests/scenarios --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html
```

To skip the multi_node_scheduling tests which are run in a multi-node cluster where some
hosts have more resources than others in order to test VM scheduling behavior
```console
tox -r -e py36 -- harvester_e2e_tests/scenarios --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html -m "not multi_node_scheduling"
```

To run just the multi_node_scheduling tests
```console
tox -r -e py36 -- harvester_e2e_tests/scenarios --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html -m muti_node_scheduling
```

To run the scenario tests in a Python3.8 environment:
```console
tox -r -e py38 -- harvester_e2e_tests/scenarios --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html
```
By default the tests will cleanup after themselves. If you want to preserve the
test artifact for debugging purposes, you may specific the `--do-not-cleanup`
flag. For example:
```console
tox -r -e py38 -- harvester_e2e_tests/scenarios --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html --do-not-cleanup
```

## Running delete Host tests
----------------------------

To run the delete_host tests at the end when all tests are done running
```console
tox -e py36 -- harvester_e2e_tests/apis --endpoint https://<harvester_node_0 IP>:30443 --harvester_cluster_nodes 1 --html=test_result.html -m delete_host
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

