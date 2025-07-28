from __future__ import annotations

import asyncio
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ulauncher.utils.dbus_trigger_event import dbus_trigger_event

if TYPE_CHECKING:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

logger = logging.getLogger(__name__)

# Import other modules within functions to avoid circular deps and make sure the logger is initialized


def get_argument_type(input_arg: str) -> Literal["id", "url", "path", "invalid"]:
    """
    Derives the type of input argument (url, path, id or invalid).
    """
    if input_arg.startswith(("http", "git@")):
        return "url"
    if input_arg.startswith("file:///") and Path(input_arg[7:]).exists():
        return "path"
    if "/" in input_arg and Path(input_arg).exists():
        return "path"
    from ulauncher.modes.extensions import extension_finder

    if extension_finder.locate(input_arg):
        return "id"
    if Path(input_arg).exists():
        return "path"
    return "invalid"


def normalize_path(path: str) -> str:
    if path.startswith("file://"):  # Pathlib does not handle this prefix
        path = path[7:]
    return str(Path(path).resolve())


def get_controller_for_input(input_arg: str) -> ExtensionController | None:
    """
    Returns an ExtensionController instance based on the input argument.
    Handles both extension ID and URL.
    """
    from ulauncher.modes.extensions.extension_controller import ExtensionController

    arg_type = get_argument_type(input_arg)
    if arg_type == "id":
        return ExtensionController.create(input_arg)
    if arg_type == "url":
        return ExtensionController.create_from_url(input_arg)
    if arg_type == "path":
        return ExtensionController.create_from_url(normalize_path(input_arg))
    return None


def list_active_extensions(_: ArgumentParser, __: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

    for controller in ExtensionController.iterate():
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)
    if not ExtensionController.iterate():
        logger.info("No extensions installed.")

    return True


def install_extension(parser: ArgumentParser, args: Namespace) -> bool:
    if "input" not in args or not args.input:
        logger.error("Error: URL or path is required for installing an extension")
        parser.print_help()
        return False

    try:
        controller = get_controller_for_input(args.input)
        if not controller:
            logger.error("Error: Invalid URL or path '%s'", args.input)
            return False
        if controller.is_installed:
            return upgrade_extensions(parser, args)
        asyncio.run(controller.install())

        dbus_trigger_event("extension:reload", [controller.id])
    except Exception:
        logger.exception("Failed to install extension")
        return False

    return True


def uninstall_extension(parser: ArgumentParser, args: Namespace) -> bool:
    if "input" not in args or not args.input:
        logger.error("Error: ID or URL is required for uninstalling an extension")
        parser.print_help()
        return False

    # Handle both extension ID and URL
    try:
        controller = get_controller_for_input(args.input)
        if not controller or not controller.is_installed:
            logger.error("Error: Could not find extension '%s'", args.input)
            return False
        asyncio.run(controller.remove())
    except Exception:
        logger.exception("Failed to uninstall extension '%s'", args.input)
        return False

    return True


def upgrade_extensions(_: ArgumentParser, args: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController, ExtensionNotFoundError

    if "input" in args and args.input:
        # Upgrade specific extension
        try:
            controller = get_controller_for_input(args.input)
            if not controller:
                logger.error("Error: Invalid URL or path '%s'", args.input)
                return False
            if not controller.is_installed:
                logger.error("Error: Extension '%s' is not installed", args.input)
                return False
            asyncio.run(controller.update())
            dbus_trigger_event("extension:reload", [controller.id])
        except ExtensionNotFoundError:
            logger.warning("Extension '%s' is not installed", args.input)
            return False
        except Exception:
            logger.exception("Failed to upgrade extension %s", args.input)
            return False

        return True

    updated_extensions = []

    for controller in ExtensionController.iterate():
        if not controller.is_manageable or not controller.state.url:
            continue

        try:
            ext_name = controller.manifest.name
            updated = asyncio.run(controller.update())
            if updated:
                updated_extensions.append(controller.id)
        except Exception:
            logger.exception("Failed to update %s", ext_name)

    if len(updated_extensions) == 0:
        logger.info("All extensions are up to date")
    else:
        dbus_trigger_event("extension:reload", updated_extensions)
        logger.info("Successfully updated %s extensions", len(updated_extensions))

    return True
