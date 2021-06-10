# About 
---
This is a harvester test framework which uses python pytest library. This framework heavily depends on the pytest fixtures which are defined in conftest.py

## Pre-requisites
-------------

Before running these tests, bring up a virtual harvester environment following the instructions in repo https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester

In addition, the tests are executed via [tox][tox] so make sure it is installed,
either via [Python pip][pip] or vendor package manager.

## Pytest Fixtures
-------------
They help us set up some helper code that should run before any tests are executed, and are perfect for setting-up resources that are needed by the tests. They are defined in conftest.py under the apis folder.

These fixture are executed at the session level and they are used to provide the authentication and to get the api endpoints before executing tests for a particular api

## Running Tests 
---

To run all the API tests under the `apis` folder, maintain the count of
harvester_cluster_nodes(1 for single node and 3 for 3-node cluster) in config.yml. It can also be set as an option while executing the pytest.

For the first time logging pass the --set-admin-password option. For subsequest runs remove this option. 

As mentioned before, the test will be executed via the [tox][tox]
environments. Currently, both Python3.6 and Python3.8 are supported.

For example, to run the tests in Python3.6 environmentfor the first time,
against a freshly installed single node Harvester:
```console
tox -e py36 -- apis --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html
```

To pass the harverster_cluster_nodes as option:
```console
tox -e py36 -- apis --endpoint https://<harvester_node_0 IP>:30443 --harvester_cluster_nodes 1 --html=test_result.html
```

To run the API tests in Python3.8 environment:
```console
tox -e py38 -- apis --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html
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

