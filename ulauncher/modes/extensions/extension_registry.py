from __future__ import annotations

import logging
from pathlib import Path
from shutil import move, rmtree
from typing import Any, Callable, Iterator, Protocol

from ulauncher import paths
from ulauncher.gi import GLib
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_record import ExtensionRecord, PreviewExtensionRecord
from ulauncher.modes.extensions.extension_remote import ExtensionRemote

logger = logging.getLogger(__name__)


def _run_gio_blocking(start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None]) -> Any:
    """Drive a callback-based Gio operation to completion synchronously on the calling thread.

    The registry's install/update flows run either in a worker thread (the preferences UI's
    ExtensionHandlers) or on the CLI's main thread, neither of which runs a GLib main loop.
    Gio.Subprocess callbacks dispatch on a GLib main context, so without a running loop they would
    never fire. A private GLib main loop (pushed as the thread-default context) drives the operation
    to completion. Remove this once these call paths run on the main GLib loop.
    """
    context = GLib.MainContext.new()
    context.push_thread_default()
    box: dict[str, Any] = {}
    completed = False
    try:
        loop = GLib.MainLoop.new(context, False)

        def finish(result: Any = None, error: Exception | None = None) -> None:
            nonlocal completed
            box["result"], box["error"] = result, error
            completed = True
            loop.quit()

        start(finish, lambda error: finish(error=error))
        # done() can fire synchronously during start() (e.g. an immediate validation failure
        # that calls back without spawning a subprocess). Then loop.quit() already ran before
        # loop.run(), which GLib does not treat as a pending quit, so running the loop would
        # block forever. Only enter the loop while the callback is still pending.
        if not completed:
            loop.run()
    finally:
        # Always restore the thread-default context, even if start() raises synchronously
        # (a synchronous raise propagates to the caller, matching the pre-conversion behavior).
        context.pop_thread_default()
    if box.get("error"):
        raise box["error"]
    return box.get("result")


def _swap_dir(new_dir: str, target: str) -> bool:
    """Replace `target` with `new_dir`, rolling back to the original on failure. Returns whether it succeeded."""
    previous = f"{new_dir}.bak"
    # A stale .bak would be an existing dir, so move() nests target inside it instead of replacing.
    rmtree(previous, ignore_errors=True)
    backed_up = False
    if Path(target).exists():
        try:
            move(target, previous)
            backed_up = True
        except OSError:
            logger.exception("Could not back up the current version of %s; keeping it in place", target)
            rmtree(new_dir, ignore_errors=True)
            return False
    try:
        move(new_dir, target)
    except OSError:
        logger.exception("Could not swap extension into %s; keeping the previous version", target)
        # A cross-device move can fail after partially creating target; clear it before restoring.
        rmtree(target, ignore_errors=True)
        if backed_up:
            try:
                move(previous, target)
            except OSError:
                logger.exception("Could not restore the previous version of %s; it remains at %s", target, previous)
        rmtree(new_dir, ignore_errors=True)
        return False
    rmtree(previous, ignore_errors=True)
    return True


class ExtensionLifecycle(Protocol):
    """The running-process operations install/uninstall need. Only the ExtensionService
    (app runtime) runs extension, so ExtensionRegistry should no-op (_NoLifecycle)."""

    def is_running(self, record: ExtensionRecord) -> bool: ...

    def start_extension(self, record: ExtensionRecord) -> bool: ...

    def stop_extension(self, record: ExtensionRecord) -> None: ...


class _NoLifecycle:
    def is_running(self, _record: ExtensionRecord) -> bool:
        return False

    def start_extension(self, _record: ExtensionRecord) -> bool:
        return False

    def stop_extension(self, _record: ExtensionRecord) -> None: ...


class ExtensionRegistry:
    """Finds installed extensions, hands out records for them, and runs the remote
    operations (install, update, uninstall).

    Instantiated exactly once per runtime. The CLI creates a plain instance. The app instead uses
    ExtensionService, a subclass that also resolves the previewed extension from its dev path and
    owns the running extension processes.
    """

    # Previews only exist in the app process; ExtensionService sets this (see preview_ext).
    preview: PreviewExtensionRecord | None = None

    def __init__(self, lifecycle: ExtensionLifecycle | None = None) -> None:
        self._lifecycle = lifecycle or _NoLifecycle()

    def get(self, ext_id: str) -> ExtensionRecord | None:
        if self.preview and self.preview.id == ext_id:
            return self.preview
        path = extension_finder.locate(ext_id)
        return ExtensionRecord(ext_id, path) if path else None

    def iterate(self, sort: bool = False) -> Iterator[ExtensionRecord]:
        records = {ext_id: ExtensionRecord(ext_id, path) for ext_id, path in extension_finder.iterate()}
        if self.preview:
            records[self.preview.id] = self.preview

        if not sort:
            yield from records.values()
            return

        def sort_key(record: ExtensionRecord) -> int:
            if record.is_preview:
                return 0
            if record.has_error:
                return 2
            if not record.is_enabled:
                return 3
            return 1

        yield from sorted(records.values(), key=sort_key)

    def install(self, url: str, commit_hash: str | None = None) -> ExtensionRecord:
        logger.info("Installing extension: %s", url)
        remote = ExtensionRemote(url)
        if Path(remote.target_dir).exists():
            logger.info('Extension with URL "%s" is already installed. Updating', remote.url)

        record = ExtensionRecord(remote.ext_id, remote.target_dir)
        self._install_from_remote(record, remote, commit_hash, url=url)
        logger.info("Extension %s installed successfully", record.id)
        return record

    def uninstall(self, record: ExtensionRecord) -> None:
        if record.is_manageable:
            self._lifecycle.stop_extension(record)
        if not record.remove():
            return
        # A still-locatable extension after removal is a non-manageable copy (e.g. distro-packaged).
        # Disable it rather than let it silently take over the removed extension's id.
        fallback_path = extension_finder.locate(record.id)
        if fallback_path:
            fallback_record = ExtensionRecord(record.id, fallback_path)
            # TODO: Try to avoid accessing state attribute
            fallback_record.state.save(is_enabled=False)
            logger.info(
                "Non-manageable extension with the same id exists in '%s'. It was kept disabled.",
                fallback_path,
            )

    def update(self, record: ExtensionRecord) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        logger.debug("Checking for updates to %s", record.id)
        has_update, commit_hash = self.check_update(record)
        if not has_update:
            logger.info('Extension "%s" is already on the latest version', record.id)
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            record.id,
            record.state.commit_hash[:8],
            commit_hash[:8],
        )

        try:
            self._install_from_remote(record, ExtensionRemote(record.state.url), commit_hash)
        except (ext_exceptions.ExtensionError, OSError):
            logger.exception("Could not update extension '%s'", record.id)
            raise
        logger.info("Successfully updated extension: %s", record.id)
        return True

    def check_update(self, record: ExtensionRecord) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = _run_gio_blocking(ExtensionRemote(record.state.url).get_compatible_hash)
        has_update = record.state.commit_hash != commit_hash
        return has_update, commit_hash

    def _install_from_remote(
        self, record: ExtensionRecord, remote: ExtensionRemote, commit_hash: str | None, **extra_state: Any
    ) -> None:
        """Install (atomically): download, then swap into place.

        A running instance is left alone: it keeps serving from the code it already loaded until the
        launcher window next closes and stops it, after which the next query starts the new version.

        `extra_state` is merged into the saved state (install records the source url; update adds nothing).
        """
        target_path = record.path
        # Fixed path per extension so failed installs don't accumulate.
        # Concurrent installs of the same id clobber each other (wouldn't have worked anyway).
        staging_dir = str(Path(paths.EXTENSIONS_STAGING) / record.id)
        rmtree(staging_dir, ignore_errors=True)
        Path(staging_dir).mkdir(parents=True)
        remote.target_dir = staging_dir

        try:
            downloaded_hash, commit_timestamp = _run_gio_blocking(
                lambda on_success, on_error: remote.download(on_success, on_error, commit_hash)
            )
            _run_gio_blocking(ExtensionDependencies(remote.ext_id, staging_dir).install)

            if not _swap_dir(staging_dir, target_path):
                msg = f"Failed to swap the staged extension into {target_path}"
                raise OSError(msg)
            record.save_installed_state(
                downloaded_hash, commit_timestamp, **extra_state, browser_url=remote.browser_url or ""
            )
        finally:
            rmtree(staging_dir, ignore_errors=True)
