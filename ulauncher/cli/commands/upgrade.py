from __future__ import annotations

import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_controller
from ulauncher.modes.extensions import ext_exceptions, extension_registry
from ulauncher.modes.extensions.extension_controller import ExtensionController
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)


def _log_url_error(ext_id: str, url: str, *, fatal: bool) -> None:
    log = logger.error if fatal else logger.warning
    if url.startswith(("/", "file://")):
        log(
            "Could not upgrade %s: local path '%s' no longer exists. Reinstall with: ulauncher install <new-path>",
            ext_id,
            url,
        )
    else:
        log("Could not upgrade %s: invalid URL '%s'", ext_id, url)


def _upgrade_all_extensions() -> list[str]:
    updated_extensions: list[str] = []

    for controller in extension_registry.load_all():
        if not controller.is_manageable or not controller.state.url:
            continue

        try:
            updated = controller.update()
            if updated:
                updated_extensions.append(controller.id)
        except ext_exceptions.UrlError:
            _log_url_error(controller.id, controller.state.url, fatal=False)
        except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
            logger.warning("Network error: Could not upgrade %s", controller.id)

    return updated_extensions


def upgrade_one(controller: ExtensionController) -> bool:
    try:
        updated = controller.update()
    except ext_exceptions.UrlError:
        _log_url_error(controller.id, controller.state.url, fatal=True)
        return False
    except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
        logger.error("Network error: Could not upgrade %s", controller.id)  # noqa: TRY400 - traceback is noise here
        return False
    if updated:
        dbus_trigger_event("extensions:reload", [controller.id])
    return True


def run(args: CLIArguments) -> int:
    if args.input:
        if controller := get_ext_controller(args.input):
            return 0 if upgrade_one(controller) else 1
        logger.error("Error: Argument '%s' does not match any installed extension", args.input)
        return 1

    updated_extensions = _upgrade_all_extensions()
    if updated_extensions:
        dbus_trigger_event("extensions:reload", updated_extensions)

    logger.info("\n%s extensions updated", len(updated_extensions))
    return 0
