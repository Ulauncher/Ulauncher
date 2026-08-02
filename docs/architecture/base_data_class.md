# BaseDataClass

Lightweight dict-based dataclass alternative used throughout Ulauncher.

## When to Use

Use `BaseDataClass` instead of:

- Standard `dataclasses`
- Plain `dict` (when you want named fields with defaults)
- Manual `__init__` methods with many parameters

## Example

```python
from ulauncher.data import BaseDataClass

class MyData(BaseDataClass):
    name: str = ""  # Annotate and give a default
    count: int = 0
    metadata: dict[str, str] = {}  # Deep copied on instantiation

data = MyData(name="test", count=5)
data["name"]  # Works like a dict
data.name  # Also works like an object
```

## Annotate every field

`BaseDataClass` uses PEP 681 `dataclass_transform`, so type checkers build a
keyword-only `__init__` signature from the annotated attributes:

```python
MyData(name="test")       # checked
MyData(nickname="test")   # error: unexpected keyword argument `nickname`
MyData(count="five")      # error: not assignable to parameter `count`
MyData({"name": "x"})     # error: positional, use MyData(**data) instead
```

Only annotated attributes become fields. Runtime behavior is unchanged, so an
unannotated field still works, but type checkers reject passing it.

`JsonConf` declares its own `__init__` to opt out, since it holds arbitrary keys.
Its subclasses get the checked signature again.

## Key Features

- **Inherits from dict** - Works with all dict methods (`get()`, `items()`, etc.)
- **Deep-copied defaults** - Mutable defaults (lists, dicts) are copied per instance
- **Keyword arguments only** - Type checkers require keywords for annotated fields
- **Runtime properties** - New properties can be added after instantiation

## Common Use Cases

**Structured data objects:**

```python
class SearchResult(BaseDataClass):
    name: str = ""
    description: str = ""
    icon: str = ""
    on_enter: EffectMessage | None = None
```

**Event payloads:**

```python
class QueryEvent(BaseDataClass):
    query: str = ""
    mode_id: str = ""
    timestamp: int = 0
```

**API responses:**

```python
class ExtensionManifest(BaseDataClass):
    name: str = ""
    description: str = ""
    developer_name: str = ""
    preferences: list[dict[str, Any]] = []
```
