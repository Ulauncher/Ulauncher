from __future__ import annotations

import logging
import signal
import subprocess
from pathlib import Path

from ulauncher import app_id, paths
from ulauncher.cli import CLIArguments
from ulauncher.gi import GLib
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_controller import DEBUGPY_HOST, DEBUGPY_PORT
from ulauncher.modes.extensions.extension_dependencies import ExtensionDependencies
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
from ulauncher.modes.extensions.extension_remote import parse_extension_url
from ulauncher.utils import scheduling
from ulauncher.utils.dbus import check_app_running, dbus_trigger_event

logger = logging.getLogger(__name__)


def _validate_extension_path(path: Path) -> str | None:
    if not path.exists():
        return f"Path '{path}' does not exist"
    if not path.is_dir():
        return f"Path '{path}' is not a directory"
    if not extension_finder.is_extension(str(path)):
        return f"Path '{path}' is not a valid extension directory (missing manifest.json or main.py)"
    return None


def _ensure_debugger_available() -> bool:
    try:
        import debugpy  # noqa: F401, T100  # type: ignore[import-not-found]
    except ImportError:
        logger.error(  # noqa: TRY400
            "Error: debugpy is required for --with-debugger option but is not installed.\n"
            "Install it using:\n"
            "  Debian/Ubuntu: sudo apt install python3-debugpy\n"
            "  Arch Linux: sudo pacman -S python-debugpy\n"
            "  Fedora: sudo dnf install python3-debugpy"
        )
        return False
    return True


def _validate_manifest(path: Path) -> bool:
    try:
        manifest = ExtensionManifest.load(str(path))
        manifest.validate()
        manifest.check_compatibility(verbose=True)
    except (ext_exceptions.ManifestError, ext_exceptions.CompatibilityError):
        logger.exception("Error: Extension validation failed")
        return False
    except ext_exceptions.ExtensionError:
        logger.exception("Error: Extension validation failed with unexpected error")
        return False
    return True


def _resolve_ext_id(path: Path) -> str | None:
    url_to_parse = str(path)
    try:
        git_url = (
            subprocess.check_output(
                ["git", "remote", "get-url", "origin"], cwd=str(path), stderr=subprocess.DEVNULL, timeout=2
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available, use path as is
        logger.debug("No git remote found, using path as URL input")
    except subprocess.TimeoutExpired:
        logger.debug("git remote lookup timed out, using path as URL input")
    else:
        if git_url:
            url_to_parse = git_url
            logger.debug("Found git remote URL: %s", git_url)

    try:
        return parse_extension_url(url_to_parse).ext_id
    except (ValueError, ext_exceptions.ExtensionError):
        logger.exception("Error: Failed to parse extension URL/path")
        return None


def run(args: CLIArguments) -> int:
    """
    Run an extension in preview mode (without installing it).
    Returns 0 on success, non-zero otherwise.
    """
    if not check_app_running(app_id):
        logger.error("Error: Ulauncher needs to be running in order to preview extensions.")
        return 1

    if args.with_debugger and not _ensure_debugger_available():
        return 1

    path = Path(args.path).resolve()
    if validation_error := _validate_extension_path(path):
        logger.error("Error: %s", validation_error)
        return 1

    if not _validate_manifest(path):
        return 1

    resolved_id = _resolve_ext_id(path)
    if resolved_id is None:
        return 1
    ext_id: str = resolved_id
    logger.info("Extension ID: %s", ext_id)

    loop = GLib.MainLoop()
    exit_code = 0

    def start_preview() -> None:
        dbus_trigger_event("extensions:preview_ext", ext_id, str(path), args.with_debugger)
        logger.info(
            "Previewing extension '%s'.\nSee its output along with Ulauncher's in %s",
            ext_id,
            paths.LOG_FILE,
        )
        if args.with_debugger:
            logger.info(
                "Connect your debugger to: %s:%d\n"
                "See https://github.com/Ulauncher/Ulauncher/wiki/How-to-debug-an-extension for instructions.",
                DEBUGPY_HOST,
                DEBUGPY_PORT,
            )
        logger.info("Press Ctrl+C to stop previewing extension '%s'...", ext_id)

    def on_deps_error(error: Exception) -> None:
        nonlocal exit_code
        logger.error("Error: Failed to install extension dependencies: %s", error)
        exit_code = 1
        loop.quit()

    def begin() -> None:
        # Runs under the loop so a synchronous install callback can quit it without racing loop.run().
        if (path / "requirements.txt").is_file():
            logger.info("Installing extension dependencies in the '.dependencies' folder...")
            ExtensionDependencies(ext_id, str(path)).install(lambda _stdout: start_preview(), on_deps_error)
        else:
            start_preview()

    def on_interrupt() -> bool:
        logger.info("Stopping '%s'...", ext_id)
        dbus_trigger_event("extensions:stop_preview")
        loop.quit()
        return False

    # The dependency install is callback-based and must finish before the app launches the extension,
    # so the CLI drives it (and Ctrl+C) on its own GLib loop.
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, on_interrupt)
    scheduling.run_when_idle(begin)
    loop.run()
    return exit_code
