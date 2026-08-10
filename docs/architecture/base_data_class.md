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
MyData(name="test")  # checked
MyData(nickname="test")  # error: unexpected keyword argument `nickname`
MyData(count="five")  # error: not assignable to parameter `count`
MyData({"name": "x"})  # error: positional, use MyData(**data) instead
```

Only annotated attributes become fields. Runtime behavior is unchanged, so an
unannotated field still works, but type checkers reject passing it.

`JsonConf` declares its own `__init__` to opt out, since it holds arbitrary keys.
Its subclasses get the checked signature again.

## Choosing a field's default

Except for `JsonConf`, `BaseDataClass` subclasses live in-memory only and may use
required fields.

They may also default to None. But avoid using None as the default when dealing
with untrusted data (json or user input) or primitive types. None is great as a
fallback for a strict `Literal["a", "b", "c"]` type but adds nothing but confusion
to a string that can be empty and must be falsy checked anyway.

## Declared props can't be dropped

A prop declared without a default is required by the generated `__init__`, so
removing it later leaves the instance contradicting its own type. The dict
methods that can do that are marked deprecated for type checkers:

```python
data.pop("name")  # error
data.popitem()  # error
data.clear()  # error
del data["name"]  # error
```

None of this is enforced at runtime.

`JsonConf` re-declares `clear` to opt back in. File data is partial, so every
prop of a file-backed class needs a default, which is exactly what `clear`
restores.

### Gaps

Writes are not covered, only removals:

```python
del data.name  # not reported
data["count"] = "5"  # not reported
data.update({"count": 5})  # not reported
```

No type checker routes the `del` statement through `__delattr__`, so the marker
on it never fires.

The other two would need per-key value types, which nothing outside `TypedDict`
synthesizes. A class can be parametrised by a hand-written companion `TypedDict`
to get them checked, but that means declaring every prop twice, in two places
that drift apart. Attribute access stays fully checked either way, so prefer
`data.count = 5` over the dict API when the key is known.

The `# error` labels above are what pyrefly reports. Other checkers may be weaker
(as of writing this, this includes ty and Pyright).

## Key Features

- **Inherits from dict** - All the read methods work (`get()`, `items()`, etc.).
  The ones that drop props are rejected, see above.
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
