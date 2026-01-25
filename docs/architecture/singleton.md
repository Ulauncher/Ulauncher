# Singleton Pattern

Use for classes that should only have one instance throughout the application lifecycle (app state, managers, registries).

## When to Use

Use singletons for:
- Application state that must be shared globally
- Manager classes (extension manager, mode manager, etc.)
- Registry classes (event bus, configuration registry)
- Resource pools (connection pools, cache managers)

⚠️ **Avoid overuse** - Singletons create global state. Use dependency injection when possible.

## For GTK Classes

GTK classes need special handling due to their inheritance chain:

```python
from ulauncher.utils.singleton import get_instance

class MyApp(Gtk.Application):
    def __call__(self, *args, **kwargs):
        return get_instance(super(), self, *args, **kwargs)
```

This ensures that calling the class multiple times returns the same instance.

## For Non-GTK Classes

Use the `Singleton` metaclass:

```python
from ulauncher.utils.singleton import Singleton

class MyManager(metaclass=Singleton):
    def __init__(self):
        self.data = {}
```

Multiple instantiation attempts return the same object:

```python
manager1 = MyManager()
manager2 = MyManager()
assert manager1 is manager2  # True - same instance
```

## Common Use Cases

**Application state:**

```python
class UlauncherApp(Gtk.Application):
    def __call__(self, *args, **kwargs):
        return get_instance(super(), self, *args, **kwargs)

app = UlauncherApp()  # First call creates instance
app = UlauncherApp()  # Returns same instance
```

**Manager classes:**

```python
class ExtensionManager(metaclass=Singleton):
    def __init__(self):
        self.extensions = {}
        self.loaded = False
```

**Registry classes:**

```python
class ModeRegistry(metaclass=Singleton):
    def __init__(self):
        self.modes = []
```

## When NOT to Use

❌ Don't use singletons for:
- Classes that might need multiple instances in tests
- Classes that should be scoped to a specific context
- Simple data containers (use BaseDataClass instead)
- Stateless utility functions (use module-level functions)
