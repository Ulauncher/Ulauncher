# Guide for AI Coding Assistants

This document contains guidelines and context for AI coding assistants working on the Ulauncher codebase.

## General Guidelines

### Communication

- If you learn something from discussions that would benefit future work, suggest adding it to this document.
- When writing comments, write them for a person reading and wanting to understand the code in the future without the context of the prompt or the context window. If further clarification would be helpful to the prompter, add those to the chat/prompt response instead.
- When there are trade-offs, prefer straightforward and simple solutions, but review your own code afterwards and suggest alternatives if the code adds technical debt that can be improved by making it more modular, reusable, or easier to read or maintain.

### Planning steps

**Before starting multi-step work:**

1. **Trace the full data flow** - Follow data through all layers to understand what types flow where and why
2. **Identify the root constraint** - Find types or interfaces mixing responsibilities before refactoring
3. **Design steps that build forward** - Each step adds permanent value, no temporary scaffolding

**Each step must be self-contained and leave the codebase:**
- Passing all tests, linting, and type checking
- Runnable and functional
- Without temporary broken states or "TODO: fix in next step" code
- With complete functionality if adding features

If you find yourself adding code like "this shouldn't be called" or fallback branches "just in case," you likely need to address a root constraint first. If you can't make a step self-contained, redesign the step boundaries.

### Best practices

- For complex logic, non-obvious behavior, or public APIs, add concise docstrings. For other cases, prefer descriptive method names and skip docstrings.
- All GTK operations **must** run in the main thread. Use `GLib.idle_add()` to schedule work in the main thread.
- To keep the app from getting slower, defer loading any modules not needed for drawing the initial window. Load them lazily instead.
- Prefer code that avoids raising exceptions when possible, rather than catching them (ex: KeyErrors can be avoided by using `dict.get()`, and AttributeError can be avoided by using `getattr()` or `hasattr()`).
- Avoid catching `Exception` or `BaseException`. Doing this can hide bugs, make debugging harder, and catch `KeyboardInterrupt` and `SystemExit`. **ONLY** catch "bare" `Exception` when the exception type **cannot** be known.
- Class methods and properties not meant to be consumed/accessed externally as well as unused function arguments should be marked with a leading underscore (`_`).

### Quality assurance

- `python -m py_compile <file_paths>` - Check that edited files are valid Python syntax.
- `make format` - autoformat code before committing
- `make check` - run all linting and tests (ruff, pyrefly, typo, pytest)
- Check the Makefile for running individual linters or targeting specific paths

### Compatibility

- Minimum Python version: 3.8, but with 3.10 type hints (via `from __future__ import annotations`)

### Dependencies

**Required dependencies:**
- Python 3.8+
- GTK 3.0
- PyGObject (GTK bindings)
- pycairo (drawing)

**Optional dependencies:**
- GtkLayerShell (for Wayland layer shell support)
- python3-levenshtein (for fuzzy matching performance)
- python-xlib (X11 integration)
- ayatanaappindicator (for system tray support)
- git (for extension installation/updates)

Avoid adding new dependencies unless necessary.

---

## Code Style

### Type hints

- All method arguments and return types must have type annotations (including `-> None`)
- Use `| None` instead of `Optional[]` (Python 3.10+ style, backported via `from __future__ import annotations`, which must be at the top of the file when using these type hints)
- Use `list[T]`, `dict[K, V]` instead of `List[T]`, `Dict[K, V]`

### Logging

Use structured logging with `%s` placeholders, not f-strings:

```python
logger.info("Processing %s items for user %s", len(items), user_id)
```

### String formatting

- Use `%s` placeholders for logging (for performance)
- Use f-strings for user-facing strings
- Don't use `str.format()`

### Naming conventions

- `snake_case` for functions, methods, variables
- `PascalCase` for classes
- `UPPER_CASE` for constants

### Formatting rules

- Use **double quotes** for strings, except strings containing double quotes (use single quotes to avoid escaping)
- No trailing whitespace on any lines, including empty lines
- Use trailing commas for **multi-line** lists, dicts and function arguments
- Maximum 120 characters per line
- Run `make format` to autofix formatting issues

---

## Tests

### Writing tests

- Place tests in `tests/` directory mirroring `ulauncher/` structure
- Use `pytest` fixtures and helper functions to avoid duplication
- Mock external dependencies (file system, network, GLib)
- Test actual functionality - if you can't, remove the test and explain why in the prompt response
- No strict coverage requirements, focus on important code paths

---

## Project Structure

### Key directories

```
ulauncher/
├── api/                    # Extension API (runs in extension process)
│   ├── client/            # Socket client for extension IPC
│   └── shared/            # Shared types between Ulauncher and extensions
├── modes/                 # Modes (apps search, file browser, calculator, extensions, etc.)
│   ├── extensions/        # Extension management and communication
│   └── ...
├── ui/                    # GTK UI components
│   └── windows/           # Application windows (main, preferences)
├── utils/                 # Utility functions and helpers
│   ├── socket_msg_controller.py  # JSON message protocol over Unix sockets
│   └── timer.py                  # GLib-based timer utilities
└── internals/             # Core application logic

Key files:
- ulauncher/modes/extensions/extension_controller.py  # Manages individual extensions
- ulauncher/modes/extensions/extension_runtime.py     # Handles extension process and IPC
- ulauncher/api/client/Client.py                      # Extension-side IPC client
- ulauncher/api/extension.py                          # Base class for extensions
- ulauncher/utils/socket_msg_controller.py            # IPC message protocol
```

---

### Event bus

Use the event bus for loosely coupled communication when direct communication between modules isn't possible. Avoid overuse.

**Sender**

```python
from ulauncher.utils.eventbus import EventBus

events = EventBus()

# Emit events
events.emit("listener_namespace:something_happened", data)
```

**Listener**

```python
from ulauncher.utils.eventbus import EventBus

events = EventBus("listener_namespace")

# Subscribe with decorator
@events.on
def something_happened(data):
    print(f"Got event with data: {data}")
```

**Current namespaces**

- "app" - The UlauncherApp class
- "extensions" - The ExtensionMode class
- "extension_lifecycle" - The extension_registry module

---

## Architecture Patterns

### Mode system

Ulauncher uses a mode-based architecture where different modes are responsible for matching user input, handling queries, and activating results.

The `BaseMode` class defines the interface for these modes. Key methods include:
- `matches_query_str()`: This method determines if a particular mode should handle the current user input. It typically checks for specific keywords or patterns.
- `handle_query()`: If a mode matches the input, this method is called to process the query. It generates a list of potential results and passes them to a callback function.
- `activate_result()`: This method is invoked when a user selects one of the results. It can perform an action, such as launching an application or opening a file, or it might return new results to be displayed.
- `get_triggers()`: This method returns any trigger keywords or shortcuts associated with the mode.
- `get_fallback_results()`: This method provides results when no other mode or specific query matches are found.

UlauncherCore interacts with these modes by iterating through them to find one that matches the user's input using `matches_query_str()`. Once a match is found, `handle_query()` is called to get the results. When a user selects a result, `activate_result()` is then used to perform the corresponding action. This design allows for extensible functionality, as new modes can be created to handle different types of user input and actions without modifying the core Ulauncher application.

### Async patterns

**Use callbacks, not async/await:**
- The codebase uses callback-based patterns, not Python's async/await
- GTK operations use GLib's async patterns (e.g., `Gio.Subprocess.wait_async()`)
- Avoid using `threading.Thread` - use GLib's event loop instead when possible
- For delayed execution, use `GLib.timeout_add()` or `timer` utility

### Custom data structures

**BaseDataClass** - Lightweight dataclass alternative used throughout the codebase:

```python
from ulauncher.utils.basedataclass import BaseDataClass

class MyData(BaseDataClass):
    name = ""  # Declare with default values
    count = 0
    metadata = {}  # Deep copied on instantiation

data = MyData(name="test", count=5)
```

- Inherits from dict, works like dataclasses but supports older Python versions
- Class attributes become instance attributes with deep-copied defaults
- No positional arguments, only keyword arguments
- New properties can be added at runtime

**JsonConf** - Config file handling with instance deduplication:

```python
from ulauncher.utils.json_conf import JsonConf

class MyConfig(JsonConf):
    setting1 = "default"
    setting2 = 42

config = MyConfig.load("/path/to/config.json")
config["setting1"] = "new value"
config.save()
```

- Inherits from BaseDataClass
- Multiple `load()` calls for the same path return the same instance
- Prevents concurrent modifications from overwriting each other

### Singleton pattern

Use the `get_instance()` helper for singletons when inheriting from GTK classes:

```python
from ulauncher.utils.singleton import get_instance

class MyApp(Gtk.Application):
    def __call__(self, *args, **kwargs):
        return get_instance(super(), self, *args, **kwargs)
```

For non-GTK classes, use the `Singleton` metaclass:

```python
from ulauncher.utils.singleton import Singleton

class MyClass(metaclass=Singleton):
    pass
```

---

## Extension communication

### Architecture

Extensions run in **separate processes** and communicate via Unix socket pairs with a JSON message protocol:

```
┌─────────────────────────┐                           ┌──────────────────────────┐
│   Ulauncher Process     │                           │   Extension Process      │
│                         │                           │                          │
│  ExtensionRuntime       │    Unix Socket Pair       │  Client                  │
│  ↓                      │ ←──────────────────────→  │  ↓                       │
│  SocketMsgController    │   (JSON line protocol)    │  SocketMsgController     │
│                         │                           │  ↓                       │
│                         │                           │  Extension (user code)   │
└─────────────────────────┘                           └──────────────────────────┘
```

**IPC implementation:**
- Uses `socket.socketpair()` to create connected Unix sockets
- Parent (Ulauncher) keeps one socket, spawns extension process with child socket FD in environment
- Messages are JSON objects separated by newlines
- `SocketMsgController` handles JSON serialization/deserialization over GLib streams asynchronously

---
