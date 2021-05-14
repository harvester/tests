# About 
---
This is a harvester test framework which uses python pytest library. This framework heavily depends on the pytest fixtures which are defined in conftest.py

## Pre-requisites
-------------

Before running these tests, bring up a virtual harvester environment following the instructions in repo https://github.com/harvester/ipxe-examples/tree/main/vagrant-pxe-harvester

## Pytest Fixtures
-------------
They help us set up some helper code that should run before any tests are executed, and are perfect for setting-up resources that are needed by the tests. They are defined in coftest.py under the apis folder.

These fixture are executed at the session level and they are used to provide the authentication and to get the api endpoints before executing tests for a particular api

## Running Tests 
---

- Create a python virtual environment, for example: test_venv
```shell
python3 -m venv test_venv
source test_venv/bin/activate
pip install -r test-requirements.txt
```

- Running tests
```shell
To run all the tests under apis folder
env PYTHONWARNINGS="ignore:Unverified HTTPS request" ./test_venv/bin/python -m pytest ./apis --endpoint https://<harvester_node_0 IP>:30443 --html=test_result.html

Example Output:
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

- Destroy the python vitual environment
```shell
deactivate
rm -rf test_env
```

## Adding New tests
--------------------

Add new api tests under the apis folder. Pytest expects tests to be located in files whose names begin with test_ or end with _test.py

Add any new fixtures in conftest.py. Fixture functions are created by marking them with the @pytest.fixture decorator. Test functions that require fixtures should accept them as arguments. 
