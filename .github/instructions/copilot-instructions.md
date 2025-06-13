---
applyTo: '**'
---

## Must Do

- When writing **integration tests**, refer to the existing tests under the `tests/harvester_e2e_tests/integrations` directory.
- When writing **API tests**, refer to the existing tests under the `tests/harvester_e2e_tests/apis` directory.
- If you mention "shared in the class" or "sharing in the class", make sure the `@pytest.fixture` scope is set to `class`. Use a `yield` statement to define the shared fixture.
- Each test case **must include at least one passing and one failing scenario**.
- **All comments must be written in English** — do not use other languages.

### Must Do for Harvester API

- When adding a new Harvester API and the corresponding resource **does not already exist** under `apiclient/harvester_api/managers`, create a new file with the **plural form** of the resource name.
- Load the new resource in `apiclient/harvester_api/api.py` and register it in `apiclient/harvester_api/managers/__init__.py`.
- Refer to `apiclient/harvester_api/managers/images.py` as a sample implementation.
- Follow these standard status codes to validate Harvester API responses:
  - `201` → Resource successfully created
  - `200` → Operation succeeded (general case)

## Don't Do

- Do **not** use method names with `_` prefixes in tests, such as `api_client.[resource]._[method]`.
- Do **not** define a function inside another function, for example:
  ```python
  def outer_function(self):
      def inner_function():
          # do something
      inner_function()
  ```
- Do **not** import libraries inside a function:
  ```python
  def function(self):
      import some_library
      # do something
  ```

## Integration Test Template

Use this template when writing a new integration test.

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

Use this structure when implementing a new Harvester API manager.

```python
import base64
from .base import BaseManager, DEFAULT_NAMESPACE


class XxxsManager(BaseManager):
    PATH_fmt = "/api/v1/namespaces/{ns}/xxx/{name}"
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
