from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.internals import theme_installer


@pytest.fixture
def theme_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Isolate the install root, state dir, staging root and clone cache in tmp_path."""
    installed = tmp_path / "themes"
    state = tmp_path / "theme_state"
    staging = tmp_path / "staging" / "themes"
    repo_cache = tmp_path / "repo-cache"
    for directory in (installed, state, staging, repo_cache):
        directory.mkdir(parents=True)
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(installed))
    monkeypatch.setattr(paths, "THEMES_STATE", str(state))
    monkeypatch.setattr(paths, "THEMES_STAGING", str(staging))
    monkeypatch.setattr(paths, "REPO_CACHE", str(repo_cache))
    return SimpleNamespace(installed=installed, state=state)


@pytest.mark.usefixtures("theme_dirs")
def test_installed_ids__unreadable_root_is_empty(mocker: MockerFixture) -> None:
    mocker.patch.object(Path, "iterdir", side_effect=OSError("denied"))
    assert theme_installer.installed_ids() == []
