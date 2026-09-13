from __future__ import annotations

import contextlib
from pathlib import Path

from ulauncher import paths
from ulauncher.data import JsonConf


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
    """The repo ids of every installed theme."""
    root = Path(paths.INSTALLED_THEMES)
    if not root.is_dir():
        return []
    # Match the loader, which tolerates unreadable paths, rather than crash
    with contextlib.suppress(OSError):
        return sorted(p.name for p in root.iterdir() if p.is_dir())
    return []
