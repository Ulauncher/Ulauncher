# JsonKeyValueConf

File-backed mapping config for JSON objects with arbitrary string keys and uniformly-typed values. Lives in `ulauncher/data/json_key_value_conf.py` alongside `JsonConf` in `ulauncher/data/json_conf.py`, sharing the same file-instance cache.

## When to Use

Use `JsonKeyValueConf[str, V]` when:

- The JSON file is a flat key/value object (not a fixed set of named fields)
- All values should be coerced to the same runtime type
- Keys are added/removed dynamically at runtime

Use [`JsonConf`](json_conf.md) instead for files with a known set of named fields.

## Example

```python
from ulauncher.data import JsonConf, JsonKeyValueConf

class Record(JsonConf):
    name = ""

class Store(JsonKeyValueConf[str, Record]):
    pass

store = Store.load("/path/to/store.json")
store["key"] = {"name": "example"}  # raw dict is coerced to Record
store.save()
```

## Key Features

- **Value coercion** — raw values (dicts, primitives) are passed through the value type's constructor on `__setitem__`. Already-correct instances are stored as-is.
- **`None`-as-delete** — assigning `None` to a key removes it instead of storing `None`.
- **Sync-on-reload** — `load()` replaces all keys with the file contents; keys absent from the file are removed from the in-memory instance. (`JsonConf.load()` merges instead — absent keys are left untouched.)
- **Instance deduplication** — same cache behaviour as `JsonConf`: multiple `load()` calls for the same path and class return the same instance.
