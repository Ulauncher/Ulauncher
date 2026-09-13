from __future__ import annotations

import contextlib
from pathlib import Path

from ulauncher import paths


def installed_ids() -> list[str]:
    """The repo ids of every installed theme."""
    root = Path(paths.INSTALLED_THEMES)
    if not root.is_dir():
        return []
    # Match the loader, which tolerates unreadable paths, rather than crash
    with contextlib.suppress(OSError):
        return sorted(p.name for p in root.iterdir() if p.is_dir())
    return []
