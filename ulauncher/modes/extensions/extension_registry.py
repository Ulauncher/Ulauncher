from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterator, Protocol

from ulauncher import paths
from ulauncher.internals.install_source import InstallSource, resolve_source
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
from ulauncher.modes.extensions.extension_record import ExtensionRecord, PreviewExtensionRecord
from ulauncher.utils.fs import StagingDir, swap_dir
from ulauncher.utils.subprocess_utils import OnError

logger = logging.getLogger(__name__)

InstallSuccess = Callable[[ExtensionRecord], None]
UpdateSuccess = Callable[[bool], None]
CheckUpdateSuccess = Callable[[bool, str], None]
Done = Callable[[], None]


class ExtensionLifecycle(Protocol):
    """The running-process operation the disk operations need: stopping before touching the
    extension's directory. Only the ExtensionService (app runtime) runs extensions, so the
    plain ExtensionRegistry no-ops (_NoLifecycle). Restarting is not part of the protocol:
    the service reconciles the process after the job wrapping the operation completes."""

    def stop_extension(self, record: ExtensionRecord, on_stopped: Callable[[], None] | None = None) -> None: ...


class _NoLifecycle:
    def stop_extension(self, _record: ExtensionRecord, on_stopped: Callable[[], None] | None = None) -> None:
        if on_stopped:
            on_stopped()


class ExtensionRegistry:
    """Finds installed extensions, hands out records for them, and runs the install
    operations (install, update, uninstall).

    Instantiated exactly once per runtime. The CLI creates a plain instance. The app instead uses
    ExtensionService, a subclass that also resolves the previewed extension from its dev path and
    owns the running extension processes.

    The install operations report back through callbacks (Gio dispatches them on the caller's
    thread-default GLib main context). Errors go to on_error, including ones detected
    synchronously, so callers have a single error path.
    """

    # Previews only exist in the app process; ExtensionService sets this (see preview_ext).
    preview: PreviewExtensionRecord | None = None

    def __init__(self, lifecycle: ExtensionLifecycle | None = None) -> None:
        self._lifecycle = lifecycle or _NoLifecycle()

    def get(self, ext_id: str) -> ExtensionRecord | None:
        if self.preview and self.preview.id == ext_id:
            return self.preview
        return self.get_installed(ext_id)

    def get_installed(self, ext_id: str) -> ExtensionRecord | None:
        """Resolve ext_id's on-disk record, ignoring any active preview overlay for it. Operations
        that touch the installed files (update, uninstall) must use this: the preview record's
        path points at a dev checkout, not the directory those operations are allowed to touch."""
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

    def install(self, url: str, on_success: InstallSuccess, on_error: OnError, commit_hash: str | None = None) -> None:
        logger.info("Installing extension: %s", url)
        source = resolve_source(url, on_error)
        if source is None:
            return
        target_dir = f"{paths.USER_EXTENSIONS}/{source.repo_id}"
        if Path(target_dir).exists():
            logger.info('Extension with URL "%s" is already installed. Updating', source.url)

        record = ExtensionRecord(source.repo_id, target_dir)

        def done() -> None:
            logger.info("Extension %s installed successfully", record.id)
            on_success(record)

        self._install_from_source(record, source, commit_hash, done, on_error)

    def uninstall(self, record: ExtensionRecord, on_done: Done, on_error: OnError) -> None:
        def remove_files() -> None:
            try:
                removed = record.remove()
            except OSError as error:
                on_error(error)
                return
            if removed:
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
            on_done()

        if record.is_manageable:
            self._lifecycle.stop_extension(record, remove_files)
        else:
            remove_files()

    def update(self, record: ExtensionRecord, on_success: UpdateSuccess, on_error: OnError) -> None:
        """Reports True to on_success if the extension was updated, False if it was already up-to-date."""
        logger.debug("Checking for updates to %s", record.id)

        def on_checked(has_update: bool, commit_hash: str) -> None:
            if not has_update:
                logger.info('Extension "%s" is already on the latest version', record.id)
                on_success(False)
                return

            logger.info(
                'Updating extension "%s" from commit %s to %s',
                record.id,
                record.state.commit_hash[:8],
                commit_hash[:8],
            )

            def done() -> None:
                logger.info("Successfully updated extension: %s", record.id)
                on_success(True)

            def fail(error: Exception) -> None:
                logger.error("Could not update extension '%s'", record.id, exc_info=error)
                on_error(error)

            update_url = record.update_url
            if update_url != record.state.url:
                logger.info("Extension %s is updated from %s, which its manifest declares", record.id, update_url)

            source = resolve_source(update_url, fail)
            if source is None:
                return
            self._install_from_source(record, source, commit_hash, done, fail)

        self.check_update(record, on_checked, on_error)

    def check_update(self, record: ExtensionRecord, on_success: CheckUpdateSuccess, on_error: OnError) -> None:
        """Reports whether a new compatible version exists, and its commit hash."""
        source = resolve_source(record.update_url, on_error)
        if source is None:
            return

        def on_hash(commit_hash: str) -> None:
            on_success(record.state.commit_hash != commit_hash, commit_hash)

        source.get_compatible_hash(on_hash, on_error)

    def install_from_staging(
        self,
        source: InstallSource,
        staging_dir: str,
        commit_hash: str,
        commit_timestamp: float,
        on_success: InstallSuccess,
        on_error: OnError,
    ) -> None:
        """Finish an install whose repo is already downloaded into staging_dir, which the caller owns.

        The CLI downloads once into pending staging so it can categorize the repo before routing;
        this runs the extension half (deps, stop, swap, state) without downloading again.
        """
        ext_id = source.repo_id
        target_dir = f"{paths.USER_EXTENSIONS}/{ext_id}"
        if Path(target_dir).exists():
            logger.info('Extension with URL "%s" is already installed. Updating', source.url)
        record = ExtensionRecord(ext_id, target_dir)

        def done() -> None:
            logger.info("Extension %s installed successfully", record.id)
            on_success(record)

        self._finalize_staged(record, source, staging_dir, commit_hash, commit_timestamp, done, on_error)

    def _finalize_staged(
        self,
        record: ExtensionRecord,
        source: InstallSource,
        staging_dir: str,
        commit_hash: str,
        commit_timestamp: float,
        on_done: Done,
        on_error: OnError,
    ) -> None:
        """Deps, stop, swap, state for the staged tree. Rejects incompatible trees before the swap."""
        try:
            # Staging path is reused, so force a fresh manifest load.
            manifest = ExtensionManifest.load(staging_dir, force=True)
            manifest.check_compatibility(verbose=True)
        except (OSError, ext_exceptions.ManifestError, ext_exceptions.CompatibilityError) as error:
            on_error(error)
            return

        def on_deps_installed(_stdout: str) -> None:
            def swap_and_finish() -> None:
                error: Exception | None = None
                if swap_dir(staging_dir, record.path):
                    try:
                        # Saved together to avoid half-updated state on source change.
                        record.save_installed_state(
                            commit_hash, commit_timestamp, url=source.url, browser_url=source.browser_url or ""
                        )
                    # Must not escape: Gio callbacks swallow exceptions, hanging blocking callers.
                    except (OSError, ext_exceptions.ExtensionError) as save_error:
                        error = save_error
                else:
                    error = OSError(f"Failed to swap the staged extension into {record.path}")
                if error:
                    on_error(error)
                else:
                    on_done()

            self._lifecycle.stop_extension(record, swap_and_finish)

        ExtensionDependencies(record.id, staging_dir).install(on_deps_installed, on_error)

    def _install_from_source(
        self,
        record: ExtensionRecord,
        source: InstallSource,
        commit_hash: str | None,
        on_done: Done,
        on_error: OnError,
    ) -> None:
        """Install (atomically): download, stop and swap. Restarting is the caller's concern
        (in the app, the service reconciles once the job wrapping this operation releases).
        """
        # Fixed path per extension so failed installs don't accumulate.
        # Concurrent installs of the same id clobber each other (wouldn't have worked anyway).
        staging = StagingDir(paths.EXTENSIONS_STAGING, record.id)
        try:
            staging_dir = staging.prepare()
        except OSError as error:
            on_error(error)
            return

        def fail(error: Exception) -> None:
            staging.discard()
            on_error(error)

        def on_downloaded(download_result: tuple[str, float]) -> None:
            downloaded_hash, commit_timestamp = download_result

            def done() -> None:
                staging.discard()
                on_done()

            def finalize_failed(error: Exception) -> None:
                staging.discard()
                on_error(error)

            self._finalize_staged(
                record,
                source,
                staging_dir,
                downloaded_hash,
                commit_timestamp,
                done,
                finalize_failed,
            )

        source.download(staging_dir, on_downloaded, fail, commit_hash)
