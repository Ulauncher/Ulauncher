from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.modes.extensions import extension_service
from ulauncher.ui.app import UlauncherApp


def _backdate(path: Path, seconds_old: float = 7200) -> None:
    old = time.time() - seconds_old
    os.utime(path, (old, old))


def test_cleanup__sweeps_every_staging_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """Stale entries are pruned from every STAGING_ROOTS entry, while recent ones are kept."""
    mocker.patch.object(extension_service.ext_service, "detach_preview_log")
    roots = [tmp_path / "staging-a", tmp_path / "staging-b"]
    for root in roots:
        (root / "old-dir").mkdir(parents=True)
        (root / "old-file").write_text("stale")
        (root / "recent-dir").mkdir(parents=True)
        _backdate(root / "old-dir")
        _backdate(root / "old-file")
    monkeypatch.setattr(paths, "STAGING_ROOTS", tuple(str(root) for root in roots))

    UlauncherApp._cleanup(UlauncherApp.__new__(UlauncherApp))

    for root in roots:
        assert not (root / "old-dir").exists()
        assert not (root / "old-file").exists()
        assert (root / "recent-dir").is_dir()
