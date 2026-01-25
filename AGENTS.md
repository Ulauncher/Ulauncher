# Guide for AI Coding Assistants

Critical Ulauncher-specific patterns and constraints.

## Core Constraints

- **GTK main thread**: All GTK operations must run in the main thread. Use `GLib.idle_add()` to schedule work from other contexts.
- **Callback-based async**: Use GLib callbacks, not Python async/await. Use `GLib.timeout_add()` or the `timer` utility for delayed execution.
- **Lazy module loading**: Defer imports not needed for the initial window to keep startup fast.
- **Exception avoidance**: Prefer defensive code (`dict.get()`, `hasattr()`) over try/except when possible. Never catch bare `Exception` unless the exception type cannot be known.

## Code Quality

**Comments**: Don't comment what the code changes does (tutorial-style). Write for future maintainers reading the full code without your context. Explain the parts you don't pick up from reading the code (gotchas, workarounds, unconventional solutions etc).

**Complexity**: Prefer straightforward and simple solutions, without architectural changes. But suggest alternatives if the code adds technical debt that can be improved by making it more modular, reusable, or easier to read or maintain.

**Testing & Linting**: Run `make format` to fix formatting errors. Run `make check` for all linting and tests. Target Python 3.8+ with 3.10 type hints.

## Architecture

Use these patterns when applicable:

**EventBus** (`ulauncher.utils.eventbus.EventBus`) - Use for cross-module communication when modules can't directly reference each other (e.g., core notifying UI, registry notifying modes). See [docs/architecture/eventbus.md](docs/architecture/eventbus.md) for usage.

**BaseDataClass** (`ulauncher.utils.basedataclass.BaseDataClass`) - Use instead of dataclasses or plain dicts for structured data. See [docs/architecture/basedataclass.md](docs/architecture/basedataclass.md) for examples.

**JsonConf** (`ulauncher.utils.json_conf.JsonConf`) - Use for config files that need auto-deduplication and safe concurrent access. See [docs/architecture/jsonconf.md](docs/architecture/jsonconf.md) for examples.

**Singleton** (`ulauncher.utils.singleton.Singleton`) - Use for classes that should only have one instance (app state, managers, registries). See [docs/architecture/singleton.md](docs/architecture/singleton.md) for usage.

**Modes** - Examine `BaseMode` and existing modes in `ulauncher/modes/` when adding new query handlers. See [docs/architecture/mode-system.md](docs/architecture/mode-system.md) for the interface.

**Extension IPC** - When modifying extension communication, see [docs/architecture/extension-ipc.md](docs/architecture/extension-ipc.md) for the multi-process architecture.

## Project Layout

```
ulauncher/
├── api/          # Extension API (separate process)
├── modes/        # Query handlers (apps, files, extensions, etc.)
├── ui/           # GTK components
└── utils/        # Shared utilities
```

Key files for extensions: `modes/extensions/extension_runtime.py`, `api/client/Client.py`, `utils/socket_msg_controller.py`
