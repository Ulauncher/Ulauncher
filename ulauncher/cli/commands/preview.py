import logging
import signal
import subprocess
from pathlib import Path

from ulauncher import app_id, paths
from ulauncher.cli import CLIArguments
from ulauncher.modes.extensions import ext_exceptions, extension_finder
from ulauncher.modes.extensions.extension_manifest import ExtensionManifest
from ulauncher.modes.extensions.extension_remote import parse_extension_url
from ulauncher.utils.dbus import check_app_running, dbus_trigger_event

logger = logging.getLogger(__name__)


def run(args: CLIArguments) -> int:  # noqa: PLR0911, PLR0912, PLR0915 - intentionally single function for ease of maintenance
    """
    Run an extension in preview mode (without installing it).
    Returns 0 on success, non-zero otherwise.
    """
    if not check_app_running(app_id):
        logger.error("Error: Ulauncher needs to be running in order to preview extensions.")
        return 1

    if args.with_debugger:
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
            return 1

    path = Path(args.path).resolve()

    validation_error = None
    if not path.exists():
        validation_error = f"Path '{path}' does not exist"
    elif not path.is_dir():
        validation_error = f"Path '{path}' is not a directory"
    elif not extension_finder.is_extension(str(path)):
        validation_error = f"Path '{path}' is not a valid extension directory (missing manifest.json or main.py)"

    if validation_error:
        logger.error("Error: %s", validation_error)
        return 1

    try:
        manifest = ExtensionManifest.load(str(path))
        manifest.validate()
        manifest.check_compatibility(verbose=True)
    except (ext_exceptions.ManifestError, ext_exceptions.CompatibilityError):
        logger.exception("Error: Extension validation failed")
        return 1
    except ext_exceptions.ExtensionError:
        logger.exception("Error: Extension validation failed with unexpected error")
        return 1

    requirements_file = path / "requirements.txt"
    if requirements_file.is_file():
        logger.warning(
            (
                "The extension has a requirements.txt file. "
                "Its dependencies will be installed in the '.dependencies' folder inside the extension path."
            ),
        )

    url_to_parse = str(path)

    try:
        git_url = (
            subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=str(path), stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repository or git not available, use path as is
        logger.debug("No git remote found, using path as URL input")
    else:
        if git_url:
            url_to_parse = git_url
            logger.debug("Found git remote URL: %s", git_url)
    try:
        parsed_url = parse_extension_url(url_to_parse)
        ext_id = parsed_url.ext_id
        logger.info("Extension ID: %s", ext_id)
    except (ValueError, ext_exceptions.ExtensionError):
        logger.exception("Error: Failed to parse extension URL/path")
        return 1

    preview_message = {"ext_id": ext_id, "path": str(path), "with_debugger": args.with_debugger}
    logger.debug("Sending preview request over D-Bus: %s", preview_message)
    dbus_trigger_event("extensions:preview_ext", preview_message)

    logger.info(
        ("Extension '%s' started.\nSee extension's output along with the Ulauncher's in %s"),
        ext_id,
        paths.LOG_FILE,
    )

    if args.with_debugger:
        logger.info(
            (
                "Connect your debugger to: localhost:5678\n"
                "See https://github.com/Ulauncher/Ulauncher/wiki/How-to-debug-an-extension for instructions."
            ),
        )

    preview_ext_id = f"{ext_id}.preview"

    # Block SIGINT so sigwait() can dequeue it atomically without racing
    # with Python's default KeyboardInterrupt handler.
    signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])
    logger.info("Press Ctrl+C to stop previewing extension '%s'...", ext_id)
    signal.sigwait([signal.SIGINT])

    logger.info("Stopping '%s'...", ext_id)
    dbus_trigger_event("extensions:stop_preview", {"preview_ext_id": preview_ext_id, "original_ext_id": ext_id})

    return 0
