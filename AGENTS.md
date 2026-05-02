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

**Testing & Linting**: Target Python 3.8+ with 3.10 type hints. Run `make check-all` for all linting and tests running inside both the user environment and the docker test image which uses Python 3.8. If you can't use docker, just run `make check`. Run `make format` to fix any formatting errors.

## Architecture

Use these patterns when applicable:

**EventBus** (`ulauncher.utils.eventbus.EventBus`) - Use for cross-module communication when modules can't directly reference each other (e.g., core notifying UI, registry notifying modes). See [docs/architecture/eventbus.md](docs/architecture/eventbus.md) for usage.

**BaseDataClass** (`ulauncher.utils.base_data_class.BaseDataClass`) - Use instead of dataclasses or plain dicts for structured data. See [docs/architecture/base_data_class.md](docs/architecture/base_data_class.md) for examples.

**JsonConf** (`ulauncher.utils.json_conf.JsonConf`) - Use for config files that need auto-deduplication and safe concurrent access. See [docs/architecture/json_conf.md](docs/architecture/json_conf.md) for examples.

**JsonKeyValueConf** (`ulauncher.utils.json_conf.JsonKeyValueConf`) - Use for JSON files that are flat key/value dicts with uniformly-typed values. See [docs/architecture/json_key_value_conf.md](docs/architecture/json_key_value_conf.md) for examples.

**Modes** - Examine `Mode` and existing modes in `ulauncher/modes/` when adding new query handlers. See [docs/architecture/mode-system.md](docs/architecture/mode-system.md) for the interface.

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
