## Harvester Test

This instruction aims to explain how to write an E2E (end to end) integration and API test under [harvester_e2e_tests](../../harvester_e2e_tests/)

- When adding a new Harvester API and the corresponding resource **does not already exist** under [Harvester API Manager](../../apiclient/harvester_api/managers/), create a new file with the **plural form** of the resource name.
    - For example, if the resource is "noodle", search for `noodle` or `noodles` under [Harvester API Manager](../../apiclient/harvester_api/managers/). Refer to the [image API](../../apiclient/harvester_api/managers/images.py) or [storageclass API](../../apiclient/harvester_api/managers/storageclasses.py) examples
    - Harvester API will be used in [integration tests](../../harvester_e2e_tests/integrations/) and [API tests](../../harvester_e2e_tests/apis/)
    - Load the new resource [here](../../apiclient/harvester_api/api.py) and register it [here](../../apiclient/harvester_api/managers/__init__.py)
    - Don't need to search [rancher API](../../apiclient/rancher_api/)

- When writing **integration tests**, refer to the existing [tests directory](../../harvester_e2e_tests/integrations).
    - Refer to the [images example](../../harvester_e2e_tests/integrations/test_1_images.py)

- When writing **API tests**, refer to the existing [tests directory](../../harvester_e2e_tests/apis/).
    - Refer to the [images example](../../harvester_e2e_tests/apis/test_images.py)

- Each test case **must include at least one passing and one failing scenario**.

- Follow these standard status codes to validate Harvester API responses:
  - `201`: Resource successfully created
  - `200`: Operation succeeded (general case)
  - `422`: Operation failed 

## Test Template

Use this template when writing a new test.

When calling API, don't use underline function or `create_data` function. If need, create another function or add more parameters to extend current function.

### Shared Fixture Template

```python
@pytest.fixture(scope="module or class")
def shared_fixture():
    """
    Shared fixture for test cases.
    """
    # 1. Prepare the environment and data
    code, data = api_client.sss.xxx()

    # 2. Assert the result
    assert code == xxxx, f"Expected status code xxxx, got {code} with data: {data}"

    output = {
        "key1": "value1",
        "key2": "value2",
    }

    yield output

    # 3. Teardown if needed
    api_client.sss.teardown_method()
```

### Test Case Template

```python
@pytest.mark.p0
@pytest.mark.skip_version_if("???", reason="???")
class TestXXXX:
    """
    Test description.
    """

    @pytest.mark.p0
    def test_xxxx(self, ${some fixtures and shared_fixture}):
        """
        Test description.
        """
        # 1. Prepare the environment and data
        shared_data = shared_fixture

        # 2. Call the API
        code, data = api_client.sss.xxx()

        # 3. Assert the result
        assert code == xxxx, f"Expected status code xxxx, got {code} with data: {data}"
```

## Harvester API Manager Template

Use this template when implementing a new Harvester API manager.

```python
import base64
from .base import BaseManager, DEFAULT_NAMESPACE


class XxxsManager(BaseManager):
    PATH_fmt = "/API/v1/namespaces/{ns}/xxx/{name}"
    CREATE_fmt = "v1/harvester/xxx"

    def create_data(self, name, namespace, data, annotations=None):
        return {
            "type": "xxx",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations,
            },
        }

    def create(self, name, data, namespace=DEFAULT_NAMESPACE, annotations=None, **kwargs):
        data = self.create_data(name, namespace, data, annotations=annotations)
        return self._create(self.CREATE_fmt, json=data, **kwargs)

    def get(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(self.PATH_fmt.format(ns=namespace, name=name), raw=raw)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(self.PATH_fmt.format(ns=namespace, name=name), raw=raw)
```


## Useful Fixtures

### `ImageChecker`

After a image is created or deleted, we need to check if it's done. So, we'll use the methods in [image_checker](../../harvester_e2e_tests/fixtures/images.py) to verfify it.