from __future__ import annotations

import logging
from pathlib import Path
from shutil import move, rmtree
from typing import Any, Callable, Iterator

from ulauncher import paths
from ulauncher.gi import GLib
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_controller import ExtensionController, PreviewExtensionController
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_remote import ExtensionRemote

logger = logging.getLogger(__name__)


def _run_gio_blocking(start: Callable[[Callable[[Any], None], Callable[[Exception], None]], None]) -> Any:
    """Drive a callback-based Gio operation to completion synchronously on the calling thread.

    Temporary bridge for step one of the asyncio/threading removal: extension_remote is now
    callback-based, but the registry's install/update flows are still async and run in worker
    threads (ext_handlers) or the CLI's asyncio loop. Gio.Subprocess callbacks dispatch on a GLib
    main context, not the asyncio loop, and no GLib loop runs in those threads, so a plain
    asyncio.Future shim would never resolve. Running a private GLib main loop (pushed as the
    thread-default context) drives the operation to completion. Remove this when the registry
    becomes callback-native.
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


class ExtensionRegistry:
    """Finds installed extensions, hands out controllers for them, and runs the remote
    operations (install, update, uninstall).

    Instantiated exactly once per runtime. The CLI creates a plain instance. The app instead uses
    ExtensionService, a subclass that also resolves the previewed extension from its dev path and
    owns the running extension processes.
    """

    # Previews only exist in the app process; ExtensionService sets this (see preview_ext).
    preview: PreviewExtensionController | None = None

    def is_running(self, _controller: ExtensionController) -> bool:
        return False

    def start_extension(self, _controller: ExtensionController) -> bool:
        return False

    async def stop_extension(self, controller: ExtensionController) -> None:
        """No-op in the CLI; ExtensionService stops the running process."""

    def get(self, ext_id: str) -> ExtensionController | None:
        if self.preview and self.preview.id == ext_id:
            return self.preview
        path = extension_finder.locate(ext_id)
        return ExtensionController(ext_id, path) if path else None

    def iterate(self, sort: bool = False) -> Iterator[ExtensionController]:
        controllers = {ext_id: ExtensionController(ext_id, path) for ext_id, path in extension_finder.iterate()}
        if self.preview:
            controllers[self.preview.id] = self.preview

        if not sort:
            yield from controllers.values()
            return

        def sort_key(controller: ExtensionController) -> int:
            if controller.is_preview:
                return 0
            if controller.has_error:
                return 2
            if not controller.is_enabled:
                return 3
            return 1

        yield from sorted(controllers.values(), key=sort_key)

    async def install(self, url: str, commit_hash: str | None = None) -> ExtensionController:
        logger.info("Installing extension: %s", url)
        remote = ExtensionRemote(url)
        if Path(remote.target_dir).exists():  # noqa: ASYNC240
            logger.info('Extension with URL "%s" is already installed. Updating', remote.url)

        controller = ExtensionController(remote.ext_id, remote.target_dir)
        await self._install_from_remote(controller, remote, commit_hash, url=url)
        logger.info("Extension %s installed successfully", controller.id)
        return controller

    async def uninstall(self, controller: ExtensionController) -> None:
        if controller.is_manageable:
            await self.stop_extension(controller)
        if not controller.remove():
            return
        # A still-locatable extension after removal is a non-manageable copy (e.g. distro-packaged).
        # Disable it rather than let it silently take over the removed extension's id.
        fallback_path = extension_finder.locate(controller.id)
        if fallback_path:
            fallback_controller = ExtensionController(controller.id, fallback_path)
            # TODO: Try to avoid accessing state attribute
            fallback_controller.state.save(is_enabled=False)
            logger.info(
                "Non-manageable extension with the same id exists in '%s'. It was kept disabled.",
                fallback_path,
            )

    async def update(self, controller: ExtensionController) -> bool:
        """
        :returns: False if already up-to-date, True if was updated
        """
        logger.debug("Checking for updates to %s", controller.id)
        has_update, commit_hash = await self.check_update(controller)
        if not has_update:
            logger.info('Extension "%s" is already on the latest version', controller.id)
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            controller.id,
            controller.state.commit_hash[:8],
            commit_hash[:8],
        )

        try:
            await self._install_from_remote(controller, ExtensionRemote(controller.state.url), commit_hash)
        except (ext_exceptions.ExtensionError, OSError):
            logger.exception("Could not update extension '%s'", controller.id)
            raise
        logger.info("Successfully updated extension: %s", controller.id)
        return True

    async def check_update(self, controller: ExtensionController) -> tuple[bool, str]:
        """
        Returns tuple with commit info about a new version
        """
        commit_hash = _run_gio_blocking(ExtensionRemote(controller.state.url).get_compatible_hash)
        has_update = controller.state.commit_hash != commit_hash
        return has_update, commit_hash

    async def _install_from_remote(
        self, controller: ExtensionController, remote: ExtensionRemote, commit_hash: str | None, **extra_state: Any
    ) -> None:
        """Install (atomically): download, stop, swap and restart (if previously running).

        `extra_state` is merged into the saved state (install records the source url; update adds nothing).
        """
        target_path = controller.path
        # Fixed path per extension so failed installs don't accumulate.
        # Concurrent installs of the same id clobber each other (wouldn't have worked anyway).
        staging_dir = str(Path(paths.EXTENSIONS_STAGING) / controller.id)
        rmtree(staging_dir, ignore_errors=True)
        Path(staging_dir).mkdir(parents=True)  # noqa: ASYNC240
        remote.target_dir = staging_dir
        was_running = False

        def _should_restart() -> bool:
            # a preview extension need not and should not be restarted (runs from dev path)
            is_previewed = self.preview is not None and self.preview.id == controller.id
            return was_running and not is_previewed

        try:
            downloaded_hash, commit_timestamp = _run_gio_blocking(
                lambda on_success, on_error: remote.download(on_success, on_error, commit_hash)
            )
            _run_gio_blocking(ExtensionDependencies(remote.ext_id, staging_dir).install)

            was_running = self.is_running(controller)
            if _should_restart():
                await self.stop_extension(controller)
            if not _swap_dir(staging_dir, target_path):
                msg = f"Failed to swap the staged extension into {target_path}"
                raise OSError(msg)
            controller.save_installed_state(
                downloaded_hash, commit_timestamp, **extra_state, browser_url=remote.browser_url or ""
            )
        finally:
            rmtree(staging_dir, ignore_errors=True)
            if _should_restart():
                self.start_extension(controller)
