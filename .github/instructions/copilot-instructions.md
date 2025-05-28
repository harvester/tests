---
applyTo: '**'
---

## Must Do

- When writing integrations tests, please refer to the existing tests in `tests/harvester_e2e_tests/integrations` directory.
- When writing api tests, please refer to the existing tests in `tests/harvester_e2e_tests/apis` directory.
- When mentioning `shared in the class` or `sharing in the class` , the `@pytest.fixture` should be `class`. Then, use `yield` generator to create the shared fixture.
- Test cases should have one passed case and one failed case at least.
- All comments are written in English, please do not use other languages.


### Do with API

- When adding a new Harvester API, if the resource doesn't eixst under `apiclient/harvester_api/managers`, please create a new file under that directory with Plural form. Then, load it in `apiclient/harvester_api/api.py` and add it to the `apiclient/harvester_api/managers/__init__.py` class.
- Refer to `apiclient/harvester_api/managers/images.py` for how to implement a new API manager
- Follow these status codes to assert the Harvester API result:
    - `201` for successfully created when creating
    - `200` for success for others

## Don't do

- Do not use underscore `_` prefix method in test case, like `api_client.[resource]._[method]`
- Do not write function in the function, like this:
    ```python
    def outer_function(self):
        def inner_function():
            # do something
        inner_function()
    ```
- Do not import library in the function, like this:
    ```python
    def function(self):
        import some_library
        # do something
    ```

## Integration Test Template

When writing a new integration test, please use the following templates:

```python
## some shared fixtures 
@pytest.fixture(scope="module or class")
def shared_fixture():
    """
    Comments
    """
    # 1. Prepare the environment and data
    # 2. call API, sss is resource, xxx is the method
    code, data = api_client.sss.xxx()
    # 3. Assert the result with code (status code)
    assert code == xxxx, f"Expected status code xxxx, got {code} with data: {data}"
    output = {
        "key1": "value1",
        "key2": "value2",
    }
    yield output
    # 4. Teardown if needed
    api_client.sss.teardown_method()

@pytest.mark.p0
@pytest.mark.skip_version_if("???", reason="???")
class TestXXXX:
    """
    Comments
    """

    @pytest.mark.p0
    def test_XXXX(self, ${some fixtures and shared_fixture}):
        """
        Comments
        """
        # 1. Prepare the environment and data
        shared_data = shared_fixture
        # 2. call API, sss is resource, xxx is the method
        code, data = api_client.sss.xxx()
        # 3. Assert the result with code (status code)
        assert code == xxxx, f"Expected status code xxxx, got {code} with data: {data}"
```

### Harvester API Template

When writing a new API, please use the following template:

```python
import base64
from .base import BaseManager, DEFAULT_NAMESPACE


class xxxtManager(BaseManager):
    PATH_fmt = "/api/v1/namespaces/{ns}/xxxx/{name}"
    CREATE_fmt = "v1/harvester/xxxx"

    def create_data(self, name, namespace, data, annotations=None):
        return {
            "type": "xxxxx",
            "metadata": {
                "namespace": namespace,
                "name": name,
                "annotations": annotations
            },
        }

    def create(self, name, data, namespace=DEFAULT_NAMESPACE, annotations=None, **kwargs):
        data = self.create_data(name, namespace, data, annotations=annotations)
        return self._create(
            self.CREATE_fmt,
            json=data, **kwargs)

    def get(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._get(
            self.PATH_fmt.format(ns=namespace, name=name), raw=raw)

    def delete(self, name, namespace=DEFAULT_NAMESPACE, *, raw=False):
        return self._delete(
            self.PATH_fmt.format(ns=namespace, name=name), raw=raw)

```