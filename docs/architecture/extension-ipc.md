# Extension IPC Architecture

Extensions run in **separate processes** and communicate with Ulauncher via Unix socket pairs using a JSON-line protocol.

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
