from __future__ import annotations

import asyncio
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from shutil import copytree, rmtree
from typing import Iterator

from ulauncher import paths
from ulauncher.modes.extensions import extension_finder
from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError
from ulauncher.modes.extensions.extension_dependencies import (
    ExtensionDependencies,
    ExtensionDependenciesRecoverableError,
)
from ulauncher.modes.extensions.extension_remote import ExtensionRemote
from ulauncher.utils.singleton import Singleton

logger = logging.getLogger()


class ExtensionRegistry(metaclass=Singleton):
    """
    Singleton registry for managing all extension controllers.
    Provides centralized access to extension controllers throughout the application.
    """

    _registry: dict[str, ExtensionController]

    def __init__(self) -> None:
        self._registry = {}

    def get(self, ext_id: str) -> ExtensionController | None:
        """Get an extension controller by ID."""
        return self._registry.get(ext_id)

    def get_or_raise(self, ext_id: str) -> ExtensionController:
        """Get an extension controller by ID."""
        controller = self._registry.get(ext_id)
        if not controller:
            msg = f"Extension with ID '{ext_id}' not found in registry"
            raise ExtensionNotFoundError(msg)

        return controller

    def iterate(self) -> Iterator[ExtensionController]:
        """Iterate over all registered extension controllers."""
        yield from self._registry.values()

    def load(self, ext_id: str, path: str | None = None) -> ExtensionController:
        """Load an extension controller into in-memory registry. It doesn't run it."""
        if not path:
            path = extension_finder.locate(ext_id)
            if not path:
                # If it's already in the registry but not found on disk, it means it's been removed
                self._registry.pop(ext_id, None)

                msg = f"Extension with ID '{ext_id}' not found"
                raise ExtensionNotFoundError(msg)
        new_controller = ExtensionController(ext_id, path)
        self._registry[ext_id] = new_controller
        return new_controller

    def load_all(self) -> Iterator[ExtensionController]:
        """Load all extensions found by the extension finder into in-memory registry. It doesn't run them."""
        for ext_id, ext_path in extension_finder.iterate():
            self.load(ext_id, ext_path)

        yield from self._registry.values()

    async def install(
        self, url: str, commit_hash: str | None = None, warn_if_overwrite: bool = True
    ) -> ExtensionController:
        logger.info("Installing extension: %s", url)
        remote = ExtensionRemote(url)
        commit_hash, commit_timestamp = remote.download(commit_hash, warn_if_overwrite)

        try:
            # install python dependencies from requirements.txt
            deps = ExtensionDependencies(remote.ext_id, remote.target_dir)
            deps.install()
        except ExtensionDependenciesRecoverableError:
            # clean up broken install
            rmtree(remote.target_dir)
            raise
        else:
            controller = self.load(remote.ext_id, remote.target_dir)
            controller.state.save(
                url=url,
                browser_url=remote.browser_url or "",
                commit_hash=commit_hash,
                commit_time=datetime.fromtimestamp(commit_timestamp).isoformat(),
                updated_at=datetime.now().isoformat(),
                error_type="",
                error_message="",
            )
            logger.info("Extension %s installed successfully", controller.id)
            return controller

    async def install_preview(self, ext_id: str, path: str) -> ExtensionController:
        logger.info("Installing extension in preview: %s", path)

        # install python dependencies from requirements.txt
        deps = ExtensionDependencies(ext_id, path)
        deps.install()

        controller = self.load(ext_id, path)
        controller.state.save(
            url=path,
            browser_url=path,
            commit_hash="(preview)",
            commit_time="N/A",
            updated_at="N/A",
            error_type="",
            error_message="",
        )
        logger.info("Extension %s installed successfully", controller.id)
        return controller

    async def stop_all(self) -> None:
        """Stop all running extensions."""

        jobs = [c.stop() for c in self._registry.values() if c.is_running]
        await asyncio.gather(*jobs)

    async def remove(self, controller: ExtensionController) -> None:
        """Remove an installed extension."""

        if not controller.is_manageable:
            logger.warning(
                "Extension %s is not manageable. Cannot remove it automatically. "
                "Please remove it manually from the extensions directory: %s",
                controller.id,
                controller.path,
            )
            return

        await controller.stop()
        rmtree(controller.path)
        self._registry.pop(controller.id, None)
        logger.info("Extension %s uninstalled successfully", controller.id)

        # non-manageable extension still exists (installed elsewhere)
        if fallback_path := extension_finder.locate(controller.id):
            controller = ExtensionController(controller.id, fallback_path)
            controller.state.save(is_enabled=False)
            logger.info("Non-manageable extension with the same id exists in '%s'", fallback_path)
            return

        state_path = Path(f"{paths.EXTENSIONS_STATE}/{controller.id}.json")
        if state_path.is_file():
            state_path.unlink()

    async def update(self, controller: ExtensionController) -> bool:
        """Update an extension to the latest available version."""

        logger.debug("Checking for updates to %s", controller.id)
        has_update, commit_hash = await controller.check_update()
        was_running = controller.is_running
        if not has_update:
            logger.info('Extension "%s" is already on the latest version', controller.id)
            return False

        logger.info(
            'Updating extension "%s" from commit %s to %s',
            controller.id,
            controller.state.commit_hash[:8],
            commit_hash[:8],
        )

        # Backup extension files. If update fails, restore from backup
        with tempfile.TemporaryDirectory(prefix="ulauncher_ext_") as backup_dir:
            ext_path = controller.path
            copytree(ext_path, backup_dir, dirs_exist_ok=True)

            try:
                await controller.stop()
                await self.install(controller.state.url, commit_hash, warn_if_overwrite=False)
            except Exception:
                logger.exception("Could not update extension '%s'.", controller.id)
                copytree(backup_dir, ext_path, dirs_exist_ok=True)
                await controller.toggle_enabled(was_running)
                raise

        await controller.toggle_enabled(was_running)
        logger.info("Successfully updated extension: %s", controller.id)

        return True
