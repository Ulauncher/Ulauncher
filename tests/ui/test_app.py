from __future__ import annotations

import os
import time
from pathlib import Path
from weakref import WeakValueDictionary

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


@pytest.mark.parametrize(
    ("persistent", "backend_changed", "expect_restart"),
    [
        (True, True, True),
        (True, False, False),
        (False, True, False),
    ],
)
def test_needs_restart__only_for_persistent_processes(
    mocker: MockerFixture, persistent: bool, backend_changed: bool, expect_restart: bool
) -> None:
    """A non-persistent process just quits, so the next activation applies the change."""
    app = UlauncherApp.__new__(UlauncherApp)
    app._persistent = persistent
    app._startup_display_backend = None
    mocker.patch("ulauncher.ui.app.preferred_backend", return_value="x11" if backend_changed else None)
    # Keep the test hermetic: the real load would read the user's settings.json and could rewrite it
    mocker.patch("ulauncher.ui.app.Settings.load", return_value=mocker.Mock(display_backend="auto"))

    assert app.needs_restart() == expect_restart


def test_prefs_close__quits_normally_when_not_persistent(mocker: MockerFixture) -> None:
    app = UlauncherApp.__new__(UlauncherApp)
    app.windows = WeakValueDictionary()
    app._persistent = False
    app._startup_display_backend = None
    mocker.patch("ulauncher.ui.app.preferred_backend", return_value="x11")
    run_when_idle = mocker.patch("ulauncher.utils.scheduling.run_when_idle")
    timer = mocker.patch("ulauncher.utils.scheduling.timer")

    app._on_window_destroyed(mocker.Mock(), "preferences")

    assert app.restart_requested is False
    assert not run_when_idle.called
    assert timer.called
