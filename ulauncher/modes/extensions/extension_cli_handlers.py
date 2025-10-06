from __future__ import annotations

import asyncio
import contextlib
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from ulauncher.utils.dbus import dbus_trigger_event

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

logger = logging.getLogger(__name__)

# Import other modules within functions to avoid circular deps and make sure the logger is initialized


def get_ext_controller(input_arg: str) -> ExtensionController | None:
    """
    Parses the input argument and returns an ExtensionController instance if it's installed, otherwise None
    """
    from ulauncher.modes.extensions import extension_registry
    from ulauncher.modes.extensions.extension_controller import ExtensionNotFoundError
    from ulauncher.modes.extensions.extension_remote import parse_extension_url

    arg = normalize_arg(input_arg)
    with contextlib.suppress(ValueError):
        parse_result = parse_extension_url(arg)
        arg = parse_result.ext_id

    try:
        return extension_registry.load(arg)
    except ExtensionNotFoundError:
        return None


def normalize_arg(path: str) -> str:
    if "://" in path:
        return path
    with contextlib.suppress(OSError):
        return str(Path(path).resolve(strict=True))
    return path


def list_active_extensions(_: ArgumentParser, __: Namespace) -> bool:
    from ulauncher.modes.extensions import extension_registry

    extensions = list(extension_registry.load_all())
    for controller in extensions:
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not extensions:
        logger.info("No extensions installed.")

    return True


def install_extension(parser: ArgumentParser, args: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController
    from ulauncher.modes.extensions.extension_remote import ExtensionRemoteError, InvalidExtensionRecoverableError

    if "input" not in args or not args.input:
        logger.error("Error: URL or path is required for installing an extension")
        parser.print_help()
        return False

    if get_ext_controller(args.input):
        return upgrade_extensions(parser, args)

    url = normalize_arg(args.input)
    try:
        controller = asyncio.run(ExtensionController.install(url))
        dbus_trigger_event("extensions:reload", [controller.id])
    except (ValueError, InvalidExtensionRecoverableError):  # error already logged
        return False
    except ExtensionRemoteError:
        logger.warning("Network error: Could not install %s", args.input)
        return False
    else:
        return True


def uninstall_extension(parser: ArgumentParser, args: Namespace) -> bool:
    if "input" not in args or not args.input:
        logger.error("Error: ID or URL is required for uninstalling an extension")
        parser.print_help()
        return False

    if controller := get_ext_controller(args.input):
        asyncio.run(controller.remove())
        dbus_trigger_event("extensions:stop", [controller.id])
        return True

    logger.error("Error: Argument '%s' does not match any installed extension", args.input)
    return False


def upgrade_extensions(_: ArgumentParser, args: Namespace) -> bool:
    from ulauncher.modes.extensions import extension_registry
    from ulauncher.modes.extensions.extension_remote import ExtensionRemoteError

    if "input" in args and args.input:
        # Upgrade specific extension
        if controller := get_ext_controller(args.input):
            try:
                asyncio.run(controller.update())
            except ExtensionRemoteError:
                logger.warning("Network error: Could not upgrade %s", args.input)
            dbus_trigger_event("extensions:reload", [controller.id])
            return True
        logger.error("Error: Argument '%s' does not match any installed extension", args.input)
        return False

    updated_extensions = []

    for controller in extension_registry.load_all():
        if not controller.is_manageable or not controller.state.url:
            continue

        try:
            updated = asyncio.run(controller.update())
            if updated:
                updated_extensions.append(controller.id)
        except ExtensionRemoteError:
            logger.warning("Network error: Could not upgrade %s", controller.id)

    if updated_extensions:
        dbus_trigger_event("extensions:reload", updated_extensions)

    logger.info("\n%s extensions updated", len(updated_extensions))
    return True
