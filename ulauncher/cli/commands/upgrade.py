from __future__ import annotations

import logging
from typing import Literal

from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_record, get_ext_registry, get_theme_id, run_blocking
from ulauncher.internals import install_errors, theme_installer
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.modes.extensions.extension_record import ExtensionRecord
from ulauncher.utils.dbus import dbus_trigger_event

logger = logging.getLogger(__name__)

UpgradeOutcome = Literal["updated", "current", "failed"]


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


def _update_blocking(record: ExtensionRecord) -> bool:
    registry = get_ext_registry()
    return run_blocking(lambda done, fail: registry.update(record, done, fail))


def _upgrade_extension(record: ExtensionRecord, *, fatal: bool) -> UpgradeOutcome:
    """Upgrade one extension. Single upgrades log errors, batch upgrades log warnings and continue."""
    log = logger.error if fatal else logger.warning
    try:
        updated = _update_blocking(record)
    except install_errors.UrlError:
        _log_url_error(record.id, record.update_url, fatal=fatal)
        return "failed"
    except install_errors.NetworkError:
        log("Network error: Could not upgrade %s", record.id)
        return "failed"
    except (install_errors.InstallError, ext_exceptions.ExtensionError, OSError):
        # update() already logged the details; keep the batch going for the other extensions
        log("Could not upgrade %s", record.id)
        return "failed"
    return "updated" if updated else "current"


def upgrade_one(record: ExtensionRecord) -> bool:
    if not record.is_manageable:
        logger.error("Extension %s is externally managed and can not be upgraded (%s)", record.id, record.path)
        return False
    outcome = _upgrade_extension(record, fatal=True)
    if outcome == "updated":
        dbus_trigger_event("extensions:reload", [record.id])
    return outcome != "failed"


def upgrade_one_theme(repo_id: str) -> bool:
    outcome = _upgrade_theme(repo_id, fatal=True)
    if outcome == "updated":
        dbus_trigger_event("themes:reload")
    return outcome != "failed"


def _upgrade_theme(repo_id: str, *, fatal: bool) -> UpgradeOutcome:
    """Upgrade one installed theme. Single upgrades emit themes:reload via upgrade_one_theme;
    batch upgrades log warnings and continue, and run() reloads once for the whole batch."""
    log = logger.error if fatal else logger.warning
    state = theme_installer.load_state(repo_id)
    if not state.url:
        # A theme copied in by hand has no source to check against
        log("Could not upgrade theme %s: no source URL recorded", repo_id)
        return "failed"
    try:
        has_update, commit_hash = run_blocking(lambda done, fail: theme_installer.check_update(repo_id, done, fail))
        if not has_update:
            logger.info('Theme "%s" is already on the latest version', repo_id)
            return "current"
        logger.info('Updating theme "%s" from commit %s to %s', repo_id, state.commit_hash[:8], commit_hash[:8])
        run_blocking(lambda done, fail: theme_installer.download(state.url, done, fail, commit_hash))
    except install_errors.UrlError:
        log("Could not upgrade theme %s: invalid URL '%s'", repo_id, state.url)
        return "failed"
    except install_errors.NetworkError:
        log("Network error: Could not upgrade theme %s", repo_id)
        return "failed"
    except (install_errors.InstallError, OSError) as e:
        # Unlike the extension path, nothing logs the details, so this is the only output
        log("Could not upgrade theme %s: %s", repo_id, e)
        return "failed"
    return "updated"


def run(args: CLIArguments) -> int:
    if args.input:
        # Same collision case as uninstall: one id can exist in both stores.
        # Upgrade both so batch and single upgrades agree.
        record = get_ext_record(args.input)
        theme_id = get_theme_id(args.input)
        if not record and not theme_id:
            logger.error("Error: Argument '%s' does not match any installed extension or theme", args.input)
            return 1
        exit_code = 0
        if record and not upgrade_one(record):
            exit_code = 1
        if theme_id and not upgrade_one_theme(theme_id):
            exit_code = 1
        return exit_code

    records = [record for record in get_ext_registry().iterate() if record.is_manageable and record.update_url]
    updated_extensions = [record.id for record in records if _upgrade_extension(record, fatal=False) == "updated"]
    if updated_extensions:
        dbus_trigger_event("extensions:reload", updated_extensions)

    # Same as extensions: a theme without a recorded source (e.g. copied in by hand) is not upgradeable
    theme_ids = [repo_id for repo_id in theme_installer.installed_ids() if theme_installer.load_state(repo_id).url]
    updated_themes = [repo_id for repo_id in theme_ids if _upgrade_theme(repo_id, fatal=False) == "updated"]
    if updated_themes:
        dbus_trigger_event("themes:reload")

    logger.info("\n%s extensions and %s themes updated", len(updated_extensions), len(updated_themes))
    return 0
