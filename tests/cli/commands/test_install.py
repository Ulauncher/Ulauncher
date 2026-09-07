from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.cli import CLIArguments
from ulauncher.cli.commands import install
from ulauncher.internals import install_errors

INSTALL_URL = "https://example.com/user/repo"


def test_run__download_failure__leaves_pending_staging_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """A failed CLI install must not leave its per-repo dir behind in PENDING_STAGING."""
    pending = tmp_path / "pending"
    pending.mkdir()
    monkeypatch.setattr(paths, "PENDING_STAGING", str(pending))
    # The failure path must not touch the real install roots
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(tmp_path / "no-themes"))
    monkeypatch.setattr(paths, "USER_EXTENSIONS", str(tmp_path / "no-extensions"))

    class FakeSource:
        repo_id = "test-failed-install"
        url = INSTALL_URL

        def __init__(self, url: str) -> None:
            assert url == INSTALL_URL

        def download(
            self,
            _target_dir: str,
            _on_success: Callable[[tuple[str, float]], None],
            on_error: Callable[[Exception], None],
            _commit_hash: str | None = None,
        ) -> None:
            on_error(install_errors.InstallError("boom"))

    mocker.patch.object(install, "InstallSource", FakeSource)

    assert install.run(CLIArguments(input=INSTALL_URL)) == 1
    assert list(pending.iterdir()) == []
