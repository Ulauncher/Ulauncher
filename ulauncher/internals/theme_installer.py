from __future__ import annotations

import contextlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from shutil import rmtree
from typing import Callable

from ulauncher import paths
from ulauncher.data import Err, JsonConf
from ulauncher.internals import install_errors
from ulauncher.internals.install_source import categorize, clear_repo_cache, resolve_source
from ulauncher.utils.fs import StagingDir, swap_dir
from ulauncher.utils.subprocess_utils import OnError

logger = logging.getLogger(__name__)

ThemeInstalled = Callable[[str], None]  # receives the installed repo_id
CheckUpdateSuccess = Callable[["tuple[bool, str]"], None]  # (has_update, commit_hash)


class ThemeState(JsonConf):
    url: str = ""
    commit_hash: str = ""
    commit_time: str = ""
    updated_at: str = ""


def _state_path(repo_id: str) -> str:
    return f"{paths.THEMES_STATE}/{repo_id}.json"


def load_state(repo_id: str) -> ThemeState:
    return ThemeState.load(_state_path(repo_id))


def installed_dir(repo_id: str) -> str:
    return f"{paths.INSTALLED_THEMES}/{repo_id}"


def installed_ids() -> list[str]:
    """The repo ids of every installed theme. Staging lives outside the install root, so no names are excluded."""
    root = Path(paths.INSTALLED_THEMES)
    if not root.is_dir():
        return []
    # An unreadable root is not "no themes": match the loader, which ignores unreadable dirs, rather than crash
    with contextlib.suppress(OSError):
        return sorted(p.name for p in root.iterdir() if p.is_dir())
    return []


def finalize_install(staging_dir: str, repo_id: str, url: str, commit_hash: str, commit_timestamp: float) -> None:
    """Swap a staged repo into place as a theme and record its install state.

    Rejects the staged tree before the swap when it is not a theme. Installs and updates converge
    here, so an update whose remote HEAD changed kind fails while the installed theme stays intact.

    :raises ulauncher.internals.install_errors.InstallError: if the staged tree is not a theme.
    :raises OSError: if the staged tree cannot be swapped into place or the state cannot be recorded.
    """
    kind = categorize(staging_dir)
    if isinstance(kind, Err):
        raise install_errors.InstallError(kind.error)
    if kind.value != "theme":
        # "extension" is the only other kind categorize() can report on Ok
        msg = f"{url} is an extension, not a theme"
        raise install_errors.InstallError(msg)
    target = installed_dir(repo_id)
    if not swap_dir(staging_dir, target):
        msg = f"Failed to swap the staged theme into {target}"
        raise OSError(msg)
    state = load_state(repo_id)
    if not state.save(
        url=url,
        commit_hash=commit_hash,
        commit_time=datetime.fromtimestamp(commit_timestamp, timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
    ):
        # Reporting failure beats reporting an install that upgrades would later break on stale state
        msg = f"Failed to save the theme state of {repo_id}"
        raise OSError(msg)


def uninstall(repo_id: str) -> bool:
    """Remove an installed theme repo and its state. Returns whether the directory existed.

    :raises OSError: if the theme directory cannot be removed.
    """
    target = Path(installed_dir(repo_id))
    existed = target.is_dir()
    if existed:
        # Not ignore_errors: the caller must report a failed removal rather than a successful uninstall
        rmtree(target)
    Path(_state_path(repo_id)).unlink(missing_ok=True)
    # The JsonConf cache keeps the state instance alive - clearing it ensures the old data won't resurface
    load_state(repo_id).clear()
    # The bare-clone cache is disposable and keyed by repo id; drop it so the disk is reclaimed
    clear_repo_cache(repo_id)
    return existed


def download(url: str, on_success: ThemeInstalled, on_error: OnError, commit_hash: str | None = None) -> None:
    """Download a theme repo into staging and install it, reporting its repo_id.

    Installs and updates share this path (an update is a download pinned to the new hash); both go
    through finalize_install, so the kind re-check there covers a remote HEAD that changed kind.
    """
    logger.info("Installing theme: %s", url)
    source = resolve_source(url, on_error)
    if source is None:
        return
    # Fixed path per theme so failed installs don't accumulate.
    # Concurrent installs of the same id clobber each other (wouldn't have worked anyway).
    staging = StagingDir(paths.THEMES_STAGING, source.repo_id)
    try:
        staging_dir = staging.prepare()
    except OSError as error:
        on_error(error)
        return

    def fail(error: Exception) -> None:
        staging.discard()
        on_error(error)

    def on_downloaded(result: tuple[str, float]) -> None:
        downloaded_hash, commit_timestamp = result
        try:
            finalize_install(staging_dir, source.repo_id, source.url, downloaded_hash, commit_timestamp)
        except (OSError, install_errors.InstallError) as error:
            fail(error)
            return
        staging.discard()
        logger.info("Theme %s installed successfully", source.repo_id)
        on_success(source.repo_id)

    source.download(staging_dir, on_downloaded, fail, commit_hash)


def check_update(repo_id: str, on_success: CheckUpdateSuccess, on_error: OnError) -> None:
    """Report whether the installed theme's remote has a newer HEAD, and that commit hash."""
    state = load_state(repo_id)
    source = resolve_source(state.url, on_error)
    if source is None:
        return

    def on_hash(latest_hash: str) -> None:
        on_success((state.commit_hash != latest_hash, latest_hash))

    source.get_compatible_hash(on_hash, on_error)
