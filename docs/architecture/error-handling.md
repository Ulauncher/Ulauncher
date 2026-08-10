# Error Handling

The goal: a bug in one feature degrades that feature, never the app, and every failure is
logged exactly once with its traceback. No Python tool can track exception propagation
statically, so the policy leans on a small set of structural rules instead of per-function
annotations.

## Barriers

A barrier is a place where control enters our code from the outside (the GLib main loop, a
Gio async callback, a subprocess result, an IPC message). An exception that escapes through
a barrier is dumped to stderr by PyGObject, bypassing our logging, and can kill the source
that dispatched it.

Barriers catch `Exception` and log with `logger.exception`. They live in the dispatchers,
not in the callbacks:

- `scheduling.Context._trigger` covers everything scheduled via `timer`, `interval`, and
  `run_when_idle`.
- `EventBus.emit` covers all event listeners, and isolates listeners from each other.

Code running under these dispatchers must not add its own catch-all. Raising to the barrier
is the designed error path. Add a local try/except only to act on a specific expected error.

GTK signal handlers are not centrally dispatched. PyGObject already contains their
exceptions (printed to stderr, the loop survives), so they are an accepted gap.

## Boundary error types

A subsystem's public functions may raise only its own error family (for extensions:
`ExtensionError` and its subclasses in `ext_exceptions`), `OSError`, or nothing. Internals
raise freely and the subsystem's public surface translates.

This is what makes callee changes safe: the contract callers depend on is the error type at
the boundary, not the concrete exceptions inside. Specific errors may be broadened when
crossing outward (a `ManifestError` may surface as `ExtensionError`, file errors as
`OSError`), never narrowed.

Document the contract with a `:raises` docstring on the public function. This is prose for
humans. No linter verifies that callers honor it, and DOC502 flags documented-but-propagated
errors as extraneous, so the DOC rules stay off.

## Errors as values

Callback chains model failure as a value through their `on_error` parameter: the caller is
forced to provide the failure path up front, so failure handling cannot be forgotten.

For synchronous functions where failure is an expected outcome the caller must branch on
(bad user input, an invalid file), return `Fallible` from `ulauncher.data` instead of raising.
This is the only contract a type checker enforces: `Ok`/`Err` form a union with no `unwrap`,
so the value is unreachable until the caller narrows with `isinstance`. A callee change
cannot silently widen the failure surface, it changes the return type and the checker flags
every caller.

```python
from ulauncher.data import Err, Fallible, Ok


def parse_port(raw: str) -> Fallible[int, str]:
    if not raw.isdigit():
        return Err(f"Not a number: {raw}")
    return Ok(int(raw))


result = parse_port(user_input)
if isinstance(result, Err):
    return notify(result.error)
use(result.value)
```

Do not use `Fallible` wholesale. Code that cannot reasonably fail should just return its
value, and unexpected failures (a bug, a full disk mid-write) should raise and travel to
the barrier.

## Rules of thumb

- Never catch bare `except:`. It swallows `KeyboardInterrupt` and `SystemExit`.
- Prefer guard clauses (`is_file()`, `hasattr()`) over try/except when the check is cheap.
- Catch a specific type only where you act on it differently, and catch it where that
  decision belongs.
- Never catch-and-log in mid-layers "just in case". That logs the failure twice or hides it
  from the caller. Let it travel to the barrier or the boundary.
