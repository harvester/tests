# Table Of Contents

- [Overview](#overview)
- [Test Documentation](#test_document)
    - [Add New Test Document](#new_test_doc)
    - [Generating the test doc sites](#generating_docs)
- [Backend Tests](#backend)
    - [Prerequisites](#prerequisites)
    - [Configure Options in config.yml](#configure_options)
        - [Deprecated Config Options](#deprecated_config)
        - [Minimal Config Options](#minimal_config)
        - [Image Config Options](#image_config)
        - [Network Config Options](#network_config)
        - [Backup Config Options](#backup_config)
        - [Host Config Options](#host_config)
        - [Terraform Config Options](#terraform_config)
        - [Rancher Integration Config Options](#rancher_config)
    - [Run Tests](#run_tests)
    - [Contribute](#contribute)
        - [Add New Tests](#add_new_test)
- [Frontend Tests](#frontend)
    - [Generating test skeletons](#generating_skels)


# Overview <a name="overview" />
This repository contains the Harvester backend (pytest) test, frontend (cypress) test and test documentation.  You can look into the part that you are interested in.



# Test Documentation <a name="test_document"/>
The manual test cases are accessible [here](https://harvester.github.io/tests/manual/).

Some scenarios are hard to test using the automation tests and are documented as manual test cases that need to be verified before release.

The manual test case pages can be edited under `docs/content/manual/`.


## Add New Test Document <a name="new_test_doc"/>
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
Related issue: https://github.com/harvester/harvester/issues/#id

Description of the test case.
```

Both of these files can contain Markdown in the title and page body.


## Generating the test doc sites <a name="generating_docs" />
You can generate all of the test sites locally with the `Makefile`. There are a few of pre-requisites for it to work.
- golang and [Hugo](https://gohugo.io/getting-started/installing/)
- python3 and pip
- nodejs and npm

The makefile allows you to do the following
- `make all`
     - This will create all of the docs sites and put them into `docs/public/`
- `make run-docs`
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



# Backend Tests <a name="backend"/>
The end-to-end backend test implemented using Python [pytest][pytest] framework, relying on Harvester's API calls.
All test cases placed under `harvester_e2e_tests`, with following convention:
    - `apis/` fundamental test cases which only relying on Harvester cluster and its API.
    - `integrations/` general test cases relying on external resource accessibility.  Most test cases are placed in here and need several configuration options inputted by `config.yml`
    - `scenarios/` test cases to fit specific scenarios.


## Prerequisites <a name="prerequisites" />
- Existing Harvester cluster
- Python3, version >= `3.6`
- tox (optional)

The (e2e) tests are expected to be ran against a given Harvester cluster. In addition, the tests are executed via [tox][tox] so make sure it is installed, either via [Python pip][pip] or vendor package manager.


## Configure Options in config.yml <a name="configure_options" />
The section is targeting to explain configure options and test cases depends on.
Notice that configuration options in [config.yml](config.yml) can be overwritten by command line parameters.
For example, to overwrite the `endpoint` option, we can use the `--endpoint` parameter while running the tests. 

### Deprecated Config Options <a name="deprecated_config" />
- `do-not-cleanup`
- `harvester_cluster_nodes`
- `backup-scripts-location`
- `rancher-version`

### Minimal Config Options <a name="minimal_config" />
- `endpoint` for Harvester API endpoint
- `username` for Harvester Dashboard username, it is fixed as `admin`
- `password` for Harvester Dashboard password
- `wait_timeout` Waiting time (seconds) for any test steps need to wait state change or polling

### Image Config Options <a name="image_config" />
- `image-cache-url`
- `win-image-url`

While running the tests, the image fixtures will attempt to create the test images by providing the download URLs for the various cloud image providers (e.g. `htps://download.opensuse.org/repositories/Cloud:/Images:/Leap_15.3/images/openSUSE-Leap-15.3.x86_64-NoCloud.qcow2`). Sometimes a given cloud image provider URL can be slow or inaccessible, which cause the underlying tests to fail. Therefore, it is recommended to create a local web server to cache the images that the tests depended on. We can then use the `--image-cache-url` parameter to convey the image cache URL to the tests. The absence of the `--image-cache-url` parameter means the tests will attempt to directly download the images directly from the cloud image providers instead.

### Network Config Options <a name="network_config" />
- `vlan-id`, be used to create **VM Network**, should be integer and in range 1 to 4094
- `vlan-nic`, be used to create **Cluster Network Config**, the NIC should be available in all nodes.

Some tests required VLAN networking. Those tests are disabled unless a VLAN ID and VLAN interface (NIC) are specified. For those tests to be successful, the VLAN routing and DHCP must be properly setup prior to running the tests. Setting up VLAN networking is infrastructure-specific, and therefore outside the scope of this document. Please work with your IT infrastructure team create the appropriate VLANs.

When using the virtual Harvester cluster (i.e. [vagrant-pxe-harvester](https://github.com/harvester/ipxe-examples)), the VLAN ID must be `1`, and the VLAN NIC must be `harvester-mgmt`.

### Backup Config Options <a name="backup_config" />
To test NFS related test cases, following Options is required:
- `nfs-endpoint`
- `nfs-mount-dir`

To test S3 related test cases, following Options is required:
- `region`
- `accessKeyId`
- `secretAccessKey`
- `bucketName`

### Host Config Options <a name="host_config" />
- `node-scripts-location`
    - most contains: `power_on.sh`, `power_off.sh`, `reboot.sh`

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

### Terraform Config Options <a name="terraform_config" />

The Harvester [terraform][terraform] test requires [terraform][terraform] CLI. Please refer to [terraform][terraform] on how to download and install the CLI.

### Rancher Integration Config Options <a name="rancher_config" />
- `rancher-endpoint`
- `rancher-admin-password`
- `rancher-cluster-wait-timeout`
- `kubernetes-version`

Optionally, in order to run the Rancher integration tests, an external Rancher cluster is also required. The Rancher integration tests are disabled unless the Rancher (API) endpoint is specified.



## Run Tests <a name="run_tests" />
Prior to running the (e2e) tests, you must edit [config.yml](config.yml) to provide the correct configuration.

You can execute tests via [tox][tox] or python command; to execute without tox, you will need to install dependencies first. (via `pip install -r test-requirements.txt`, we will recommend to use **virtual environment** for it)

Executing the tests via tox or python have a bit of difference as follows:
```bash
# execute by tox, you can use `-e py36` for executing with python3.6
tox -e py38 -- harvester_e2e_tests
# execute by python
python -m pytest harvester_e2e_tests
# in a virtual environment, you can even use `pytest` directly:
pytest harvester_e2e_tests
```

Some examples for executing dynamically:
```bash
# To generate report into html
pytest harvester_e2e_tests --html=test_result.html

# To list all tests
pytest harvester_e2e_tests --collect-only
# To list all markers
pytest harvester_e2e_tests --markers
# To list all markers for test topics
pytest harvester_e2e_tests --markers | grep related
# To list all markers for test priority
pytest harvester_e2e_tests --markers | grep priority

# To list filtered tests by marks
pytest harvester_e2e_tests --collect-only -m "hosts and p0 or images and p0"
# equals to
pytest harvester_e2e_tests --collect-only -m "p0 and (hosts or images)"
```

You can check pytest's [documentation](https://docs.pytest.org/en/latest/usage.html) for advanced usage.



## Contribute <a name="contribute" />
As we are restructuring e2e tests, please do **NOT** use following legacy codes:
- `utils.py`
- `scenarios/*`
- `fixtures/api_endpoints.py`
- `fixtures/api_version.py`
- `fixtures/backuptarget.py`
- `fixtures/image.py`
- `fixtures/keypair.py`
- `fixtures/network.py`
- `fixtures/session.py`
- `fixtures/support_bundle.py`
- `fixtures/user.py`
- `fixtures/vm.py`
- `fixtures/vm_template.py`
- `fixtures/volume.py`


### Test Skeletons
A backend test skeleton looks like this:

```python
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

### Test Fixture <a name="add_new_fixture"/>
- Shareable fixture
    - Scope must be `session` or `module`
    - Able to be tear down gracefully
    - Be placed in `fixtures/<topic_file>.py`
- Specific fixture
    - Be placed in test file

### Add New Tests <a name="add_new_test" />

Here are the general guidelines for adding a new e2e test:
- File name should starts with `test_`
- Add Markers for new Test
    - Priority markers: `p0`, `p1` and `p2`
    - At least add 1 topic marker
- New e2e Test(s) should be corresponding to **ONLY** one [manual test case][Harvester manual test cases],
    - When the Manual test case having several sub tests, use `TestClass` for it.
- ONLY update old e2e test case when corresponding manual test case going to be updated
- Any constants should be unique or inputted by configuration
- Any delay (sleep) should have explicit reason
- Make sure tear down is safe for other tests
- Tests should be using [fixtures][pytest fixtures] as much as possible as the [fixtures][pytest fixtures] should be able to clean up after themselves upon exit. Otherwise, the test must clean up whatever artifacts it creates upon exit.
    - All [fixtures][pytest fixtures] must be able to cleanup itself using the [recommended yield technique](https://docs.pytest.org/en/6.2.x/fixture.html#yield-fixtures-recommended)
- If the test requires new configurations, make sure to add them to both [config.yml](config.yml) and [harvester_e2e_tests/conftest.py](harvester_e2e_tests/conftest.py). [config.yml](config.yml) should have the default values.
    - If the sharable fixture requires configuration options, we should always check inputted value is valid or fail the fixture.



# Frontend Tests <a name="frontend"/>
Further info placed in [cypress/README.md](cypress/README.md)

### Creating test skeletons for new features/tickets <a name="generating_skels">
[Frontend test skeletons](cypress/README.md#test_skeletons)
There is a test skel spec to use as a template in `tests/cypress/skel/`.
- If you are adding a test to an existing suite like `tests/integration/login.spec.ts` then you can just use the template jsdoc and function call then add the test steps.
- If you are creating a new logical group of tests you can copy the `skel.spec.ts` file into integration or into a subdirectory if it fits more into that category then rename it appropriately
- Add the `@notImplemented` tag to the test case if it hasn't been implemented yet. This will have it shown with that tag on the static site.




[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pip.pypa.io/en/stable/
[flake8]: https://flake8.pycqa.org/en/latest/
[pytest]: https://docs.pytest.org/en/6.2.x/
[pytest fixtures]: https://docs.pytest.org/en/6.2.x/fixture.html#fixture
[pytest markers]: https://docs.pytest.org/en/6.2.x/example/markers.html
[terraform]: https://www.terraform.io/
[AWS S3]: https://aws.amazon.com/s3/
[Harvester manual test cases]: https://github.com/harvester/tests/tree/main/docs/content/manual