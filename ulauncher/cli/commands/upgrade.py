from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ulauncher.cli.commands import get_ext_controller
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.dbus import dbus_trigger_event

if TYPE_CHECKING:
    from ulauncher.cli import CLIArguments

logger = logging.getLogger(__name__)


def _warn_url_error(ext_id: str, url: str) -> None:
    if url.startswith(("/", "file://")):
        logger.warning(
            "Could not upgrade %s: local path '%s' no longer exists. Reinstall with: ulauncher install <new-path>",
            ext_id,
            url,
        )
    else:
        logger.warning("Could not upgrade %s: invalid URL '%s'", ext_id, url)


async def _upgrade_all_extensions() -> list[str]:
    from ulauncher.modes.extensions import extension_registry

    updated_extensions: list[str] = []

    for controller in extension_registry.load_all():
        if not controller.is_manageable or not controller.state.url:
            continue

        try:
            updated = await controller.update()
            if updated:
                updated_extensions.append(controller.id)
        except ext_exceptions.UrlError:
            _warn_url_error(controller.id, controller.state.url)
        except ext_exceptions.RemoteError:
            logger.warning("Network error: Could not upgrade %s", controller.id)

    return updated_extensions


def run(args: CLIArguments) -> bool:
    if args.input:
        if controller := get_ext_controller(args.input):
            try:
                asyncio.run(controller.update())
            except ext_exceptions.UrlError:
                _warn_url_error(controller.id, controller.state.url)
                return False
            except ext_exceptions.RemoteError:
                logger.warning("Network error: Could not upgrade %s", args.input)
                return False
            dbus_trigger_event("extensions:reload", [controller.id])
            return True
        logger.error("Error: Argument '%s' does not match any installed extension", args.input)
        return False

    updated_extensions = asyncio.run(_upgrade_all_extensions())
    if updated_extensions:
        dbus_trigger_event("extensions:reload", updated_extensions)

    logger.info("\n%s extensions updated", len(updated_extensions))
    return True
