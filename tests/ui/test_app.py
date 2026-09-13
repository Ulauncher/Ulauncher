from __future__ import annotations

import os
import time
from pathlib import Path
from weakref import WeakValueDictionary

import pytest
from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.data import Err, Ok
from ulauncher.modes.extensions import extension_service
from ulauncher.ui.app import UlauncherApp
from ulauncher.utils.systemd_controller import SystemdUnitStatus


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
    restart = mocker.patch("ulauncher.ui.app.UlauncherApp._restart")
    timer = mocker.patch("ulauncher.utils.scheduling.timer")

    app._on_window_destroyed(mocker.Mock(), "preferences")

    restart.assert_not_called()
    assert timer.called


@pytest.mark.parametrize(
    ("active", "known", "restart_accepted", "expect_restart", "expect_quit", "expect_reexec"),
    [
        (True, True, True, True, True, False),
        (True, True, False, True, False, False),
        (False, False, False, True, False, False),
        (False, True, False, False, True, True),
    ],
)
def test_restart__decides_by_unit_state(
    mocker: MockerFixture,
    active: bool,
    known: bool,
    restart_accepted: bool,
    expect_restart: bool,
    expect_quit: bool,
    expect_reexec: bool,
) -> None:
    app = UlauncherApp.__new__(UlauncherApp)
    app.restart_requested = False
    controller = mocker.patch("ulauncher.utils.systemd_controller.SystemdController").return_value
    controller.status.return_value = (
        Ok(SystemdUnitStatus(["ActiveState=active"] if active else [])) if known else Err("unknown")
    )
    controller.restart.return_value = Ok(None) if restart_accepted else Err("rejected")
    run_when_idle = mocker.patch("ulauncher.utils.scheduling.run_when_idle")

    app._restart()

    assert controller.restart.called == expect_restart
    if expect_restart:
        controller.restart.assert_called_once_with(no_block=True)
    assert run_when_idle.called == expect_quit
    assert app.restart_requested == expect_reexec
