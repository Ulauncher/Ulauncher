# Extension IPC Architecture

Extensions run in **separate processes** as the same user as Ulauncher (not sandboxed). They communicate with Ulauncher via Unix socket pairs using a JSON-line protocol.

## Architecture Diagram

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

## Key Components

**Ulauncher side:**

- `ExtensionRuntime` (`modes/extensions/extension_runtime.py`) - Manages extension process lifecycle
- `ExtensionController` (`modes/extensions/extension_controller.py`) - Coordinates extension behavior
- `SocketMsgController` (`utils/socket_msg_controller.py`) - JSON message protocol handler

**Extension side:**

- `Client` (`api/client/Client.py`) - Extension IPC client
- `Extension` (`api/extension.py`) - Base class for extension implementations

## IPC Details

**Socket creation:**

- `socket.socketpair()` creates connected Unix domain sockets
- Parent (Ulauncher) keeps one socket, spawns child (extension) with the other
- Child socket FD passed via environment variable

**Message protocol:**

- JSON objects separated by newlines (`\n`)
- Each message is a complete JSON object on a single line
- Bidirectional communication (both processes send/receive)

**Async handling:**

- `SocketMsgController` uses GLib's async I/O streams (non-blocking)
- Messages dispatched to registered handlers by message type

## Message Flow Example

1. User types extension keyword → Ulauncher sends query via socket
2. Extension processes query → sends result items back via socket
3. User selects result → Ulauncher sends action event via socket
4. Extension handles action → may send new results back

All communication is asynchronous using GLib's event loop.

## Partial (Streamed) Responses

Extension listeners that return a generator stream their results progressively: the
accumulated results are sent as responses marked `"partial": true`, throttled to at most
one per `ULAUNCHER_PARTIAL_RESPONSE_INTERVAL` seconds (default 0.1), followed by a final
unmarked, unthrottled response with the complete list. Yields landing within the
interval are not lost: they are included in the next response — the next partial, or the
final one if nothing else is yielded. Ulauncher keeps the response callback alive until
the final response, so each partial replaces the rendered list.

`ULAUNCHER_PARTIAL_RESPONSES=1` is exported by the app when spawning extension
processes. `ULAUNCHER_PARTIAL_RESPONSE_INTERVAL` is only read by the extension process
from its inherited environment — a tuning knob the app never sets.

Yielding a `Result` appends it to the streamed list; yielding a `list[Result]` replaces
it, so producers can update results they already sent (e.g. an LLM answer growing as
tokens arrive). If the generator raises, the error is logged and the accumulated results
are sent as the final response, so the request always terminates.

This only happens when the app advertises support via the `ULAUNCHER_PARTIAL_RESPONSES=1`
environment variable; otherwise generators are collected into a single response, because
older apps treat the first response as final. Stale partials are discarded through the
existing `request_id` check; when newer input supersedes the request, the extension stops
consuming the generator and sends nothing more — not even a final response.

Primary use case: extensions backed by slow producers (LLM APIs, network searches) that
can render results as they arrive.
