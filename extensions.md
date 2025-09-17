Here’s a one‑sentence summary of each class under ulauncher/modes/extensions:

  - ExtensionTrigger (extension_mode.py): A Result subclass used to represent searchable extension trigger items in the UI.
  - ExtensionMode (extension_mode.py): The Ulauncher mode that manages extension lifecycle, routes queries to extensions, and handles their actions via the socket server.
  - ExtensionSocketServer (extension_socket_server.py): A singleton Gio socket service that accepts extension connections, registers socket controllers, and routes queries/events/
  responses between the app and extensions.
  - ExtensionSocketController (extension_socket_controller.py): Manages one extension’s JSON‑framed socket connection, debounces and sends events, and forwards extension responses to
  the app event bus.
  - ExtensionRuntime (extension_runtime.py): Launches and supervises an extension subprocess via Gio, streaming stderr and invoking an error handler on exit or startup failures.
  - ExtensionRemoteError (extension_remote.py): Generic error for unexpected remote/URL handling failures.
  - InvalidExtensionRecoverableError (extension_remote.py): Recoverable error indicating the provided extension URL/path is invalid.
  - ExtensionNetworkError (extension_remote.py): Network‑related error when accessing a remote extension repository.
  - UrlParseResult (extension_remote.py): A small data container for parsed extension URL info (id, remote URL, browser URL, download template).
  - ExtensionRemote (extension_remote.py): Parses extension URLs, determines compatible versions, and downloads/exports extension code from Git hosts or local paths.
  - ExtensionDependenciesRecoverableError (extension_dependencies.py): Recoverable error indicating dependency installation failed.
  - ExtensionDependencies (extension_dependencies.py): Detects and installs an extension’s Python dependencies into a local target directory.
  - ExtensionPreference (extension_controller.py): Runtime preference model extending the manifest preference with a current value.
  - ExtensionTrigger (extension_controller.py): Trigger model derived from the manifest trigger, used within the controller.
  - ExtensionState (extension_controller.py): Persistent per‑extension state (id, URLs, commit info, enabled/error flags) stored as JSON.
  - ExtensionController (extension_controller.py): Core manager for an extension’s manifest, preferences/triggers, install/update/remove, and process runtime start/stop.
  - ExtensionNotFoundError (extension_controller.py): Error raised when an extension cannot be found by id/path.
  - ExtensionManifestError (extension_manifest.py): Error for invalid extension manifest structure/content.
  - ExtensionIncompatibleRecoverableError (extension_manifest.py): Recoverable error for extensions incompatible with the current API version.
  - ExtensionManifestPreference (extension_manifest.py): Strongly‑typed manifest entry describing one user preference (type, defaults, bounds/options).
  - ExtensionManifestTrigger (extension_manifest.py): Manifest entry describing an extension trigger (name, description, keyword, icon).
  - ExtensionManifest (extension_manifest.py): Loads, normalizes, and validates manifest.json, including API compatibility checks and v2→v3 compatibility handling.