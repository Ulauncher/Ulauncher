from __future__ import annotations

import asyncio
import contextlib
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING

from ulauncher import app_id
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


def preview_extension(_: ArgumentParser, args: Namespace) -> bool:  # noqa: PLR0911 - intentionally single function for ease of maintenance
    """
    Run an extension in preview mode (without installing it).
    Returns True on success, False otherwise.

    Implement preview extension command.
    See extension_cli_handlers.py.
    Start with the first undone point (marked as 👉).
    Work on it and then mark ✅ when you're done.
    Rest will be done in a separate session.

    TODO:
    ✅ Check if ulauncher is running. If not, print error and exit:
    ✅ Validate provided "path" (extension manifest, etc.)
    ✅ Get extension id (if it's a git-enabled path, generate it from URL)
    ✅ Call a remote dbus method that will do the points below.
        At this stage only create the necessary methods and function calls.
    --- the next steps happen in the main process in that `preview_ext()` dbus method ---
    ✅ If extension with the same ID is running, stop it.
    ✅ Run extension from the given path in "preview" mode (no install):
        Find out how extensions are run.
        Make the necessary changes to run from an arbitrary given path.
        Extensions can have dependencies listed in requirements.txt. We still need to install those.
        Create a temporary venv under `/tmp/ulauncher/{ext_id}.venv` and install dependencies there.
        Don't delete the folder because the user might want to run extension in preview mode multiple times.
        But make a note in code comments that this is intentionally left undeleted.
    ⬜ If --with-debugger, run in debugger mode. Show how to connect with a debugger
    --- back in the CLI process ---
    ⬜ On `ctrl+c`, stop extension and re-enable previous version (if any)
    ⬜ Show a special label on Preferences UI for extension running in preview mode
    """
    # Check if Ulauncher is running
    if not check_app_running(app_id):
        logger.error("Error: Ulauncher is not running. Please start it first.")
        return False

    # Validate provided path
    if not hasattr(args, "path") or not args.path:
        logger.error("Error: Extension path is required")
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

    # Trigger preview over D-Bus (stub implementation in main process for now)
    with_debugger = getattr(args, "with_debugger", False)
    preview_message = {"ext_id": ext_id, "path": str(path), "with_debugger": with_debugger}
    logger.debug("Sending preview request over D-Bus: %s", preview_message)
    dbus_trigger_event("extensions:preview_ext", preview_message, wait=True)

    # TODO: Remaining implementation steps happen in the main process handler (see extension_socket_server.preview_ext)
    return True
