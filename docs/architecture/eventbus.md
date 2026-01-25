# Event Bus

Use for cross-module communication when modules can't directly reference each other (avoid circular imports, decouple core from UI, etc.).

## Usage

**Emit events:**

```python
from ulauncher.utils.eventbus import EventBus

events = EventBus()
events.emit("listener_namespace:something_happened", data)
```

**Subscribe to events:**

```python
from ulauncher.utils.eventbus import EventBus

events = EventBus("listener_namespace")

@events.on
def something_happened(data):
    # Handle event
    pass
```

## Current Namespaces

- `"app"` - The UlauncherApp class
- `"extensions"` - The ExtensionMode class
- `"extension_lifecycle"` - The extension_registry module

## When to Use

✅ Use when:
- Module A needs to notify module B, but A can't import B (circular dependency)
- Multiple modules need to react to the same event
- Decoupling UI from core logic

❌ Avoid when:
- Direct function calls would work (simpler)
- Only one listener will ever exist (use callbacks instead)
