from __future__ import annotations

import logging

from ulauncher import paths
from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import get_ext_registry, normalize_install_arg, run_blocking
from ulauncher.data import Err
from ulauncher.internals import install_errors, theme_installer
from ulauncher.internals.install_source import InstallSource, SourceKind, categorize
from ulauncher.modes.extensions import ext_exceptions
from ulauncher.utils.dbus import dbus_trigger_event
from ulauncher.utils.fs import staging_dir

logger = logging.getLogger(__name__)


def _conflicting_kind(installing: SourceKind, repo_id: str) -> SourceKind | None:
    """The kind already installed under repo_id when it clashes with the kind being installed."""
    if installing == "theme":
        return "extension" if get_ext_registry().get(repo_id) else None
    return "theme" if repo_id in theme_installer.installed_ids() else None


def run(args: CLIArguments) -> int:
    """Install an extension or theme: download into pending staging, then route by kind.
    Both paths are idempotent, so reinstalling updates."""
    url = normalize_install_arg(args.input)
    try:
        source = InstallSource(url)
    except (ValueError, install_errors.UrlError):  # error already logged
        return 1
    try:
        with staging_dir(paths.PENDING_STAGING, source.repo_id) as staging:
            commit_hash, commit_timestamp = run_blocking(lambda done, fail: source.download(staging.path, done, fail))
            kind = categorize(staging.path)
            if isinstance(kind, Err):
                logger.error("Could not install %s: %s", args.input, kind.error)
                return 1
            if conflict := _conflicting_kind(kind.value, source.repo_id):
                article = "an" if conflict == "extension" else "a"
                logger.error(
                    "Could not install %s: already installed as %s %s. Uninstall it first",
                    args.input,
                    article,
                    conflict,
                )
                return 1
            if kind.value == "theme":
                theme_installer.finalize_install(
                    staging.path, source.repo_id, source.url, commit_hash, commit_timestamp
                )
                logger.info("Theme %s installed successfully", source.repo_id)
            else:
                record = run_blocking(
                    lambda done, fail: get_ext_registry().install_from_staging(
                        source, staging.path, commit_hash, commit_timestamp, done, fail
                    )
                )
                dbus_trigger_event("extensions:reload", [record.id])
            staging.commit()
            return 0
    except install_errors.NetworkError:
        logger.error("Network error: Could not install %s", args.input)  # noqa: TRY400 - traceback is noise
        return 1
    except (install_errors.InstallError, ext_exceptions.ExtensionError, OSError) as e:
        logger.error("Could not install %s: %s", args.input, e)  # noqa: TRY400 - traceback is noise here
        return 1
