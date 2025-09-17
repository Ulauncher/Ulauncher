from __future__ import annotations

import asyncio
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ulauncher import app_id
from ulauncher.utils.dbus import check_app_running, dbus_trigger_event

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
        return ExtensionController.create_from_id(input_arg)
    if arg_type == "url":
        return ExtensionController.create_from_url(input_arg)
    if arg_type == "path":
        return ExtensionController.create_from_url(normalize_path(input_arg))
    return None


def list_active_extensions(_: ArgumentParser, __: Namespace) -> bool:
    from ulauncher.modes.extensions.extension_controller import ExtensionController

    controllers = ExtensionController.create_all_installed()
    for controller in controllers:
        disabled_label = " [DISABLED]" if not controller.is_enabled else ""
        logger.info("- %s (%s)%s", controller.manifest.name, controller.id, disabled_label)

    if not controllers:
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

        dbus_trigger_event("extensions:reload", [controller.id])
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
        dbus_trigger_event("extensions:stop", [controller.id])
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
            dbus_trigger_event("extensions:reload", [controller.id])
        except ExtensionNotFoundError:
            logger.warning("Extension '%s' is not installed", args.input)
            return False
        except Exception:
            logger.exception("Failed to upgrade extension %s", args.input)
            return False

        return True

    updated_extensions = []

    for controller in ExtensionController.create_all_installed():
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
        dbus_trigger_event("extensions:reload", updated_extensions)
        logger.info("Successfully updated %s extensions", len(updated_extensions))

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
        At this stage only create the necessary methdos and function calls.
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
    dbus_trigger_event("extension:preview_ext", preview_message, wait=True)

    # TODO: Remaining implementation steps happen in the main process handler (see extension_socket_server.preview_ext)
    return True
