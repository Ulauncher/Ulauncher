from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from ulauncher import app_id, paths
from ulauncher.utils.dbus import check_app_running, dbus_trigger_event

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

    with contextlib.suppress(ExtensionNotFoundError):
        return extension_registry.load(arg)
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


def preview_extension(_: ArgumentParser, args: Namespace) -> bool:  # noqa: PLR0911, PLR0912, PLR0915 - intentionally single function for ease of maintenance
    """
    Run an extension in preview mode (without installing it).
    Returns True on success, False otherwise.
    """
    # Check if Ulauncher is running
    if not check_app_running(app_id):
        logger.error("Error: Ulauncher is not running. Please start it first.")
        return False

    # Validate provided path
    if not hasattr(args, "path") or not args.path:
        logger.error("Error: Extension path is required")
        return False

    # Check if debugpy is available when --with-debugger is requested
    if getattr(args, "with_debugger", False):
        try:
            import debugpy  # noqa: F401, T100  # type: ignore[import-not-found]
        except ImportError:
            logger.error(  # noqa: TRY400
                "Error: debugpy is required for --with-debugger option but is not installed.\n"
                "Install it using:\n"
                "  Debian/Ubuntu: sudo apt-get install python3-debugpy\n"
                "  Arch Linux: sudo pacman -S python-debugpy\n"
                "  Fedora: sudo dnf install python3-debugpy"
            )
            return False

    path = Path(args.path).resolve()

    # Validate path exists, is directory, and is valid extension
    validation_error = None
    if not path.exists():
        validation_error = f"Path '{path}' does not exist"
    elif not path.is_dir():
        validation_error = f"Path '{path}' is not a directory"
    else:
        # Check if it's a valid extension directory (has manifest.json and main.py)
        from ulauncher.modes.extensions import extension_finder

        if not extension_finder.is_extension(str(path)):
            validation_error = f"Path '{path}' is not a valid extension directory (missing manifest.json or main.py)"

    if validation_error:
        logger.error("Error: %s", validation_error)
        return False

    # Validate the extension manifest
    try:
        from ulauncher.modes.extensions.extension_manifest import (
            ExtensionIncompatibleRecoverableError,
            ExtensionManifest,
            ExtensionManifestError,
        )

        manifest = ExtensionManifest.load(str(path))
        manifest.validate()
        manifest.check_compatibility(verbose=True)
    except (ExtensionManifestError, ExtensionIncompatibleRecoverableError):
        logger.exception("Error: Extension validation failed")
        return False
    except Exception:
        logger.exception("Error: Extension validation failed with unexpected error")
        return False

    # Get extension ID from git URL or path
    url_to_parse = str(path)

    # Try to get git remote URL if the path is a git repository
    try:
        import subprocess

        git_url = (
            subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=str(path), stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )

        if git_url:
            url_to_parse = git_url
            logger.debug("Found git remote URL: %s", git_url)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available, use path as is
        logger.debug("No git remote found, using path as URL input")

    # Parse the URL/path to get extension ID
    try:
        from ulauncher.modes.extensions.extension_remote import parse_extension_url

        parsed_url = parse_extension_url(url_to_parse)
        ext_id = parsed_url.ext_id
        logger.info("Extension ID: %s", ext_id)
    except Exception:
        logger.exception("Error: Failed to parse extension URL/path")
        return False

    # Trigger preview over D-Bus
    with_debugger = getattr(args, "with_debugger", False)
    preview_message = {"ext_id": ext_id, "path": str(path), "with_debugger": with_debugger}
    logger.debug("Sending preview request over D-Bus: %s", preview_message)
    dbus_trigger_event("extensions:preview_ext", preview_message)

    logger.info(
        ("Extension '%s' started.\nSee extension's output along with the Ulauncher's in %s"),
        ext_id,
        paths.LOG_FILE,
    )

    if with_debugger:
        logger.info(
            (
                "Connect your debugger to: localhost:5678\n"
                "See https://github.com/Ulauncher/Ulauncher/wiki/How-to-debug-an-extension for instructions."
            ),
        )

    # Handle Ctrl+C to stop preview and re-enable previous version if any
    preview_ext_id = f"{ext_id}.preview"
    interrupted = False

    def signal_handler(_sig: int, _frame: object) -> None:
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGINT, signal_handler)

    # Wait for user to press Ctrl+C by blocking indefinitely
    logger.info("Press Ctrl+C to stop previewing extension '%s'...", ext_id)
    while not interrupted:
        time.sleep(0.1)

    logger.info("Stopping '%s'...", ext_id)

    # Send dbus event to stop preview extension and start previous one if it exists
    dbus_trigger_event("extensions:stop_preview", {"preview_ext_id": preview_ext_id, "original_ext_id": ext_id})

    return True
