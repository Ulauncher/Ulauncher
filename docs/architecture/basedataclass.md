# BaseDataClass

Lightweight dict-based dataclass alternative used throughout Ulauncher.

## When to Use

Use `BaseDataClass` instead of:
- Standard `dataclasses` (for Python 3.8 compatibility)
- Plain `dict` (when you want named fields with defaults)
- Manual `__init__` methods with many parameters

## Example

```python
from ulauncher.utils.basedataclass import BaseDataClass

class MyData(BaseDataClass):
    name = ""  # Declare with default values
    count = 0
    metadata = {}  # Deep copied on instantiation

data = MyData(name="test", count=5)
data["name"]  # Works like a dict
data.name  # Also works like an object
```

## Key Features

- **Inherits from dict** - Works with all dict methods (`get()`, `items()`, etc.)
- **Deep-copied defaults** - Mutable defaults (lists, dicts) are copied per instance
- **Keyword arguments only** - No positional args, always explicit
- **Runtime properties** - New properties can be added after instantiation
- **Type flexible** - No type enforcement, use type hints for documentation

## Common Use Cases

**Structured data objects:**
```python
class SearchResult(BaseDataClass):
    name = ""
    description = ""
    icon = None
    on_enter = None
```

**Event payloads:**
```python
class QueryEvent(BaseDataClass):
    query = ""
    mode_id = ""
    timestamp = 0
```

**API responses:**
```python
class ExtensionManifest(BaseDataClass):
    name = ""
    description = ""
    developer_name = ""
    preferences = []
```
