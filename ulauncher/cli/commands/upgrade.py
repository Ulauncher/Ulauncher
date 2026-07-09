from __future__ import annotations

import logging

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_record, get_ext_registry
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_record import ExtensionRecord

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
    registry = get_ext_registry()

    for record in registry.iterate():
        if not record.is_manageable or not record.state.url:
            continue

        try:
            updated = registry.update(record)
            if updated:
                updated_extensions.append(record.id)
        except ext_exceptions.UrlError:
            _log_url_error(record.id, record.state.url, fatal=False)
        except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
            logger.warning("Network error: Could not upgrade %s", record.id)
        except (ext_exceptions.ExtensionError, OSError):
            # update() already logged the details; keep the batch going for the other extensions
            logger.warning("Could not upgrade %s", record.id)

    return updated_extensions


def upgrade_one(record: ExtensionRecord) -> bool:
    if not record.is_manageable:
        logger.error("Extension %s is externally managed and can not be upgraded (%s)", record.id, record.path)
        return False
    try:
        get_ext_registry().update(record)
    except ext_exceptions.UrlError:
        _log_url_error(record.id, record.state.url, fatal=True)
        return False
    except (ext_exceptions.NetworkError, ext_exceptions.RemoteError):
        logger.error("Network error: Could not upgrade %s", record.id)  # noqa: TRY400 - traceback is noise here
        return False
    except (ext_exceptions.ExtensionError, OSError):
        logger.error("Could not upgrade %s", record.id)  # noqa: TRY400 - already logged in update()
        return False
    return True


def run(args: CLIArguments) -> int:
    if args.input:
        if record := get_ext_record(args.input):
            return 0 if upgrade_one(record) else 1
        logger.error("Error: Argument '%s' does not match any installed extension", args.input)
        return 1

    updated_extensions = _upgrade_all_extensions()
    logger.info("\n%s extensions updated", len(updated_extensions))
    return 0
