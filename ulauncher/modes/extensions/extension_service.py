from __future__ import annotations

import json
import logging
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol

from ulauncher import cli, paths
from ulauncher.gi import GLib
from ulauncher.internals import log_wire
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_record import (
    ExtensionErrorData,
    ExtensionExitCause,
    ExtensionRecord,
    PreviewExtensionRecord,
)
from ulauncher.modes.extensions.extension_registry import (
    Done,
    ExtensionRegistry,
    InstallSuccess,
    UpdateSuccess,
    resolve_remote,
)
from ulauncher.modes.extensions.extension_runtime import DEBUGPY_HOST, DEBUGPY_PORT, ExtensionRuntime
from ulauncher.utils import scheduling
from ulauncher.utils.eventbus import EventBus

if TYPE_CHECKING:
    from ulauncher.internals import ipc
    from ulauncher.utils.subprocess_utils import OnError

logger = logging.getLogger(__name__)
events = EventBus("extensions", skip_if_not_bound=True)

# A job holds its extension's process and directory until it calls the release callback it
# is given. Every completion path, success or error, must release.
Job = Callable[[Callable[[], None]], None]


def _releasing(callback: Callable[..., None], release: Callable[[], None]) -> Callable[..., None]:
    """Wrap a job's completion callback so release() always runs after it, success or error."""

    def wrapped(*args: Any) -> None:
        try:
            callback(*args)
        finally:
            release()

    return wrapped


class ExtensionServiceListener(Protocol):
    """What the service reports back about the extensions it runs. Implemented by ExtensionMode,
    which registers itself via ExtensionService.activate."""

    def started(self, ext_id: str) -> None: ...

    def errored(self, ext_id: str) -> None: ...

    def invalidate_cache(self) -> None: ...

    def handle_message(self, ext_id: str, message: ipc.ExtensionMessage) -> None: ...


class _ExtensionProcessState:
    """Per-extension bookkeeping for the process and the serialized jobs.
    Only ExtensionService touches it, always on the GLib main loop."""

    runtime: ExtensionRuntime | None
    record: ExtensionRecord | None  # the record the live runtime was spawned from
    pending_stop: list[Callable[[], None]] | None  # None: no stop in flight; else callbacks to fire on exit
    jobs: deque[Job]
    job_active: bool
    draining: bool

    def __init__(self) -> None:
        self.runtime = None
        self.record = None
        self.pending_stop = None
        self.jobs = deque()
        self.job_active = False
        self.draining = False


class ExtensionService(ExtensionRegistry):
    """The app's ExtensionRegistry: also owns the extension processes and handles lifecycle intents.

    Extensions only run in the app process, so only app code uses the service. The CLI does its
    disk work with a plain ExtensionRegistry and asks the app to reconcile the processes via
    D-Bus events ("extensions:reload", ...).

    The lifecycle model has two parts:

    - Desired state is derived, not stored: an extension should run iff its record resolves and
      `record.is_enabled` (which already folds in the preview overlay and the persisted error).
      `_reconcile` aligns the process with that whenever something relevant changed.
    - Operations that need exclusive access to the process and directory (install, update,
      uninstall, restarts) run as jobs, serialized per extension id. While a job holds an id,
      `_reconcile` leaves it alone; releasing the job reconciles, which re-reads the record's
      state file and starts whatever it says should run by then. This is what makes sequences
      like "disable, update, enable" run in order without every caller passing callbacks around.
      A job re-resolves its record when it starts rather than trusting the one captured at
      enqueue time, through `get_installed` rather than `get`, so an id that is being previewed
      resolves to the installed copy instead of the developer's dev checkout.

    `check_update` is inherited unchanged: it only reads the remote, so it doesn't need to hold
    the id and isn't a job.
    """

    listener: ExtensionServiceListener | None
    _preview_log: tuple[str, logging.Handler] | None

    def __init__(self) -> None:
        super().__init__(lifecycle=self)
        self._ext_states: defaultdict[str, _ExtensionProcessState] = defaultdict(_ExtensionProcessState)
        self.listener = None
        self._preview_log = None
        events.set_self(self)

    def activate(self, listener: ExtensionServiceListener) -> None:
        """
        Set the listener that lifecycle events report to, and start the enabled extensions.
        Called by ExtensionMode when the app loads its modes.
        """
        self.listener = listener
        scheduling.run_when_idle(self._start_extensions)

    def _start_extensions(self) -> None:
        # Start explicitly rather than reconcile, so extensions that errored last session
        # get retried (start_extension clears the persisted error).
        for ext in self.iterate():
            if ext.state.is_enabled:
                self.start_extension(ext)

    def is_running(self, record: ExtensionRecord) -> bool:
        state = self._ext_states.get(record.id)
        return state is not None and state.runtime is not None

    def _reconcile(self, ext_id: str) -> None:
        """Align the process with the desired state: run iff the id resolves to a record and,
        after re-reading that record's state file, it is enabled. No-op while a job holds the id
        or a stop is in flight; both reconcile again when done."""
        state = self._ext_states[ext_id]
        if state.job_active or state.pending_stop is not None:
            return
        record = self.get(ext_id)
        if record:
            record.reload_state()
        if record and record.is_enabled:
            if not state.runtime:
                self.start_extension(record)
        elif state.runtime:
            self._stop(ext_id)

    def _enqueue_job(self, ext_id: str, job: Job) -> None:
        state = self._ext_states[ext_id]
        state.jobs.append(job)
        self._run_next_job(ext_id)

    def _run_next_job(self, ext_id: str) -> None:
        """Run this id's queued jobs until one is still in flight, then reconcile if it drained.

        Jobs that release synchronously loop here rather than recursing, so a long backlog for one
        id doesn't nest a stack frame per job.
        """
        state = self._ext_states[ext_id]
        if state.draining:
            return  # the loop below owns the queue and picks up whatever is appended to it
        state.draining = True
        try:
            while not state.job_active and state.jobs:
                self._start_job(ext_id, state.jobs.popleft())
        finally:
            state.draining = False

        if not state.job_active and not state.jobs:
            self._reconcile(ext_id)

    def _start_job(self, ext_id: str, job: Job) -> None:
        state = self._ext_states[ext_id]
        state.job_active = True
        released = False

        def release() -> None:
            nonlocal released
            if released:
                return
            released = True
            state.job_active = False
            self._run_next_job(ext_id)

        # A job that raises before wiring its callbacks never releases, wedging this id's queue.
        # Release on a synchronous failure so the remaining jobs still drain.
        try:
            job(release)
        except Exception:
            logger.exception("Extension job for '%s' failed", ext_id)
            release()

    def _enqueue_restart(self, ext_id: str) -> None:
        """Queue a stop while holding the id; the reconcile on release starts whatever the
        record resolution says should run by then (installed version, preview, or nothing)."""
        self._enqueue_job(ext_id, lambda release: self._stop(ext_id, release))

    def toggle_enabled(self, record: ExtensionRecord, enabled: bool) -> None:
        record.state.save(is_enabled=enabled, error=None)
        self._reconcile(record.id)

    def install(self, url: str, on_success: InstallSuccess, on_error: OnError, commit_hash: str | None = None) -> None:
        remote = resolve_remote(url, on_error)
        if remote is None:
            return
        ext_id = remote.ext_id
        run = super().install

        def job(release: Callable[[], None]) -> None:
            run(url, _releasing(on_success, release), _releasing(on_error, release), commit_hash)

        self._enqueue_job(ext_id, job)

    def uninstall(self, record: ExtensionRecord, on_done: Done, on_error: OnError) -> None:
        run = super().uninstall

        def job(release: Callable[[], None]) -> None:
            current = self.get_installed(record.id)
            if current is None:
                error = ext_exceptions.ExtensionError(f"Extension {record.id} is no longer installed")
                _releasing(on_error, release)(error)
                return
            run(current, _releasing(on_done, release), _releasing(on_error, release))

        self._enqueue_job(record.id, job)

    def update(self, record: ExtensionRecord, on_success: UpdateSuccess, on_error: OnError) -> None:
        run = super().update

        def job(release: Callable[[], None]) -> None:
            current = self.get_installed(record.id)
            if current is None:
                error = ext_exceptions.ExtensionError(f"Extension {record.id} is no longer installed")
                _releasing(on_error, release)(error)
                return
            run(current, _releasing(on_success, release), _releasing(on_error, release))

        self._enqueue_job(record.id, job)

    def _build_launch_args(self, record: ExtensionRecord) -> tuple[list[str], dict[str, str]]:
        ext_deps = ExtensionDependencies(record.id, record.path)
        extension_main = f"{record.path}/main.py"
        cmd = [sys.executable, extension_main]

        if isinstance(record, PreviewExtensionRecord) and record.with_debugger:
            cmd = [
                sys.executable,
                "-m",
                "debugpy",
                "--listen",
                f"{DEBUGPY_HOST}:{DEBUGPY_PORT}",
                "--wait-for-client",
                extension_main,
            ]

        prefs = {p_id: pref.value for p_id, pref in record.preferences.items()}
        triggers = {t_id: t.default_keyword for t_id, t in record.manifest.triggers.items() if t.default_keyword}
        # backwards compatible v2 preferences format (with keywords added back)
        v2_prefs = {**triggers, **prefs}
        env = {
            # Assume previews should always run verbose (works until we add a log-level flag)
            "VERBOSE": str(int(cli.get_args().verbose or record.is_preview)),
            "PYTHONPATH": ":".join(x for x in [paths.APPLICATION, ext_deps.get_dependencies_path()] if x),
            "EXTENSION_PREFERENCES": json.dumps(v2_prefs, separators=(",", ":")),
            "ULAUNCHER_EXTENSION_ID": record.id,
            "ULAUNCHER_INPUT_DEBOUNCE": str(record.manifest.input_debounce),
            # v2 extensions already get a compatibility-mode warning, so only warn v3 ones.
            "ULAUNCHER_API_DEPRECATION_WARNINGS": "1" if record.manifest.supports_current_api() else "0",
        }
        return cmd, env

    def start_extension(self, record: ExtensionRecord) -> None:
        """Starts the extension in a subprocess."""
        state = self._ext_states[record.id]
        if state.runtime:
            return

        if not record.is_preview:
            record.state.save(error=None)

        if state.job_active or state.pending_stop is not None:
            # A job or in-flight stop reconciles on release, which starts the extension now
            # that the error is cleared.
            return

        def exit_handler(cause: ExtensionExitCause, error_msg: str) -> None:
            errored = cause != "Stopped"

            if errored:
                logger.error('Extension "%s" exited with an error: %s (%s)', record.id, error_msg, cause)
                state.runtime = None
                state.record = None
                # A failing preview must not disable the installed extension by persisting its error.
                if not record.is_preview:
                    record.state.save(error=ExtensionErrorData(type=cause, message=error_msg))

                # Tear down the dead preview before the drain below. The drain can reconcile,
                # and a reconcile that still saw the overlay would respawn it.
                if self.preview is record:
                    self.stop_preview()

            if listener := self.listener:
                listener.invalidate_cache()

            # Drain into a fresh list: a callback may start a new runtime for this id or queue a
            # new stop, neither of which belongs to this exit.
            callbacks = state.pending_stop or []
            state.pending_stop = None
            for on_stopped in callbacks:
                on_stopped()

            if errored and (listener := self.listener):
                listener.errored(record.id)

            # Only reconcile after an intentional stop. On error the record has the error
            # persisted (reconcile would not start it) or is a preview, which waits for an
            # explicit relaunch rather than respawn in a crash loop.
            if not errored:
                self._reconcile(record.id)

        def message_handler(message: ipc.ExtensionMessage) -> None:
            if listener := self.listener:
                listener.handle_message(record.id, message)

        try:
            record.manifest.validate()
            record.manifest.check_compatibility(verbose=True)
        except ext_exceptions.ManifestError as err:
            exit_handler("Invalid", str(err))
            return
        except ext_exceptions.CompatibilityError as err:
            exit_handler("Incompatible", str(err))
            return

        cmd, env = self._build_launch_args(record)

        # socketpair/spawnv can fail for host reasons (fd exhaustion, fork limits, missing
        # interpreter). Route these through exit_handler like a crash, so the error surfaces
        # consistently and queued stop callbacks still drain.
        try:
            state.runtime = ExtensionRuntime(record.id, cmd, env, exit_handler, message_handler)
        except (OSError, GLib.Error) as err:
            exit_handler("FailedToStart", str(err))
            return
        state.record = record
        if listener := self.listener:
            listener.invalidate_cache()
            listener.started(record.id)

    def _stop(self, ext_id: str, on_stopped: Callable[[], None] | None = None) -> None:
        state = self._ext_states[ext_id]
        if runtime := state.runtime:
            state.runtime = None
            state.record = None
            state.pending_stop = []
            if on_stopped:
                state.pending_stop.append(on_stopped)
            runtime.stop()
        elif state.pending_stop is not None:
            # a stop is already in flight, report on the same exit
            if on_stopped:
                state.pending_stop.append(on_stopped)
        elif on_stopped:
            on_stopped()

    def stop_extension(self, record: ExtensionRecord, on_stopped: Callable[[], None] | None = None) -> None:
        """Stop the extension process if it is running. Does not block: on_stopped fires once the
        process has actually exited, or immediately if it is not running."""
        state = self._ext_states.get(record.id)
        if state and state.record and state.record.is_preview and not record.is_preview:
            # A previewed extension runs from its dev path, so it must survive an install/update
            # of the installed copy: it isn't the process this call means to stop, despite the
            # shared id.
            if on_stopped:
                on_stopped()
            return
        self._stop(record.id, on_stopped)

    def send_message(self, record: ExtensionRecord, message: ipc.Event, request_id: int | None = None) -> None:
        """
        Sends a JSON message to the extension if it is running.
        """
        state = self._ext_states.get(record.id)
        if state and state.runtime:
            state.runtime.send_message(message, request_id)

    def save_user_preferences(self, record: ExtensionRecord, data: Any) -> None:
        from ulauncher.internals.ipc import EventType

        old_preferences = {p_id: pref.value for p_id, pref in record.preferences.items()}
        record.persist_preferences(data)
        for p_id, new_value in data.get("preferences", {}).items():
            # Only notify about values changing for preferences declared in the manifest
            if p_id in old_preferences and new_value != old_preferences[p_id]:
                event_data: ipc.UpdatePreferencesEvent = {
                    "type": EventType.UPDATE_PREFERENCES,
                    "args": (p_id, new_value, old_preferences[p_id]),
                }
                self.send_message(record, event_data)

    @events.on
    def reload(
        self,
        extension_ids: list[str] | None = None,
    ) -> None:
        if not extension_ids:
            logger.warning("Reload message received without any extension IDs. No extensions will be restarted.")
            return

        logger.info("Reloading extension(s): %s", ", ".join(extension_ids))
        for ext_id in extension_ids:
            # An id with neither a record nor process state has nothing to converge to, and
            # _ext_states is a defaultdict, so queueing would only leave an empty entry behind.
            if self.get(ext_id) or ext_id in self._ext_states:
                self._enqueue_restart(ext_id)

    def _attach_preview_log(self, ext_id: str) -> None:
        """Mirror the previewed extension's records to a file for the CLI that started it to tail.

        In the extensions' wire format, so the CLI restores the records and applies its own colors,
        rather than parsing them back out of a formatted line.
        """
        self.detach_preview_log()
        handler = logging.FileHandler(paths.PREVIEW_LOG_FILE, mode="w", encoding="utf-8")
        handler.setFormatter(log_wire.WireFormatter())
        # Catches the sub-loggers too, since records propagate up from "<ext_id>.<name>"
        logging.getLogger(ext_id).addHandler(handler)
        self._preview_log = (ext_id, handler)

    def detach_preview_log(self) -> None:
        """Also called on app shutdown, so a CLI tailing the log isn't left waiting for an end that
        can no longer come."""
        if self._preview_log:
            ext_id, handler = self._preview_log
            logging.getLogger(ext_id).removeHandler(handler)
            handler.close()
            # Load-bearing: dropping the file is what tells the CLI that the preview is over
            Path(paths.PREVIEW_LOG_FILE).unlink(missing_ok=True)
            self._preview_log = None

    @events.on
    def preview_ext(self, ext_id: str, path: str, with_debugger: bool = False) -> None:
        """Run an extension from a dev path WITHOUT installing it. Triggered from the CLI via D-Bus.

        While the preview is active, the record with this id launches from the dev path; its
        dependencies are installed by the CLI before this is called.
        """

        logger.info("[preview] Previewing ext_id=%s path=%s debugger=%s", ext_id, path, with_debugger)
        previous = self.preview
        self.preview = PreviewExtensionRecord(ext_id, path, with_debugger=with_debugger)
        # Attaching drops any previous handler, so the newest preview owns the log
        self._attach_preview_log(ext_id)
        if previous and previous.id != ext_id:
            # a superseded preview of another extension: converge that id back to its installed state
            self._enqueue_restart(previous.id)
        self._enqueue_restart(ext_id)

    @events.on
    def stop_preview(self) -> None:
        """Stop the active preview and restore the installed extension. Triggered from the CLI via D-Bus"""
        if not self.preview:
            # will happen if preview is interrupted before started
            logger.debug("[preview] Ignoring stop_preview; no preview active")
            return

        ext_id = self.preview.id
        logger.info("[preview] Stopping preview %s", ext_id)
        self.preview = None
        self.detach_preview_log()
        # Restore the installed extension, or leave the id stopped if it was never installed.
        self._enqueue_restart(ext_id)


ext_service = ExtensionService()
