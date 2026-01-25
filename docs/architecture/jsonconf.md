# JsonConf

Config file handling with automatic instance deduplication and safe concurrent access.

## When to Use

Use `JsonConf` for:
- User settings/preferences files
- Extension manifests and configs
- Any JSON file that multiple parts of the code might access
- Files that need automatic save debouncing

## Example

```python
from ulauncher.utils.json_conf import JsonConf

class MyConfig(JsonConf):
    setting1 = "default"
    setting2 = 42

config = MyConfig.load("/path/to/config.json")
config["setting1"] = "new value"
config.save()
```

## Key Features

- **Inherits from BaseDataClass** - All dict-like features available
- **Instance deduplication** - Multiple `load()` calls for the same path return the **same instance**
- **Safe concurrent access** - Prevents concurrent modifications from overwriting each other
- **Auto-save debouncing** - Saves are debounced to avoid excessive disk writes
- **Automatic file creation** - Creates file with defaults if it doesn't exist

## Why Instance Deduplication Matters

Without deduplication:
```python
# BAD: Two separate instances, changes conflict
config1 = MyConfig.load("/path/to/config.json")
config2 = MyConfig.load("/path/to/config.json")
config1["setting1"] = "value1"
config2["setting1"] = "value2"
config1.save()  # Writes value1
config2.save()  # Overwrites with value2 - value1 is lost!
```

With deduplication:
```python
# GOOD: Same instance, no conflicts
config1 = MyConfig.load("/path/to/config.json")
config2 = MyConfig.load("/path/to/config.json")
assert config1 is config2  # Same object!
config1["setting1"] = "value1"
config2["setting1"] = "value2"
config1.save()  # Writes value2 (both references point to same object)
```

## Common Use Cases

**User preferences:**
```python
class UserPreferences(JsonConf):
    theme = "light"
    hotkey = "<Primary>space"
    show_tray_icon = True

prefs = UserPreferences.load("~/.config/ulauncher/settings.json")
```

**Extension config:**
```python
class ExtensionConfig(JsonConf):
    api_key = ""
    refresh_interval = 300
    enabled_features = []

config = ExtensionConfig.load(f"{extension_dir}/config.json")
```
