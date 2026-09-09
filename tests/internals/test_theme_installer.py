from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from ulauncher import paths
from ulauncher.internals import install_errors, theme_installer

THEME_MANIFEST = '{"name": "x", "css_file": "theme.css"}'
EXTENSION_MANIFEST = '{"name": "x", "api_version": "3"}'
INSTALL_URL = "https://example.com/user/repo"


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


def write_theme(directory: Path, css: str = ".app {}") -> None:
    (directory / "manifest.json").write_text(THEME_MANIFEST)
    (directory / "theme.css").write_text(css)


def write_extension(directory: Path) -> None:
    (directory / "manifest.json").write_text(EXTENSION_MANIFEST)


def install_theme(repo_id: str, staging: Path, css: str = ".app {}", commit_hash: str = "oldhash") -> None:
    staging.mkdir()
    write_theme(staging, css=css)
    theme_installer.finalize_install(str(staging), repo_id, INSTALL_URL, commit_hash, 1700000000.0)


def test_finalize_install__rejects_non_theme_staged_dir(theme_dirs: SimpleNamespace, tmp_path: Path) -> None:
    unrecognized = tmp_path / "staged-unrecognized"
    unrecognized.mkdir()
    (unrecognized / "readme.txt").write_text("hello")
    with pytest.raises(install_errors.InstallError):
        theme_installer.finalize_install(
            str(unrecognized), "test_finalize_unrecognized", INSTALL_URL, "abc", 1700000000.0
        )

    extension = tmp_path / "staged-extension"
    extension.mkdir()
    write_extension(extension)
    with pytest.raises(install_errors.InstallError):
        theme_installer.finalize_install(str(extension), "test_finalize_extension", INSTALL_URL, "abc", 1700000000.0)

    assert theme_dirs.installed.exists()
    assert list(theme_dirs.installed.iterdir()) == []


@pytest.mark.usefixtures("theme_dirs")
def test_finalize_install__records_commit_and_update_time(tmp_path: Path) -> None:
    repo_id = "test_finalize_timestamps"
    staging = tmp_path / "staged-timestamps"
    staging.mkdir()
    write_theme(staging)
    theme_installer.finalize_install(str(staging), repo_id, INSTALL_URL, "abc", 1700000000.0)

    state = theme_installer.load_state(repo_id)
    assert state.commit_time == "2023-11-14T22:13:20+00:00"
    assert state.updated_at


def test_finalize_install__reports_state_save_failure(
    theme_dirs: SimpleNamespace, tmp_path: Path, mocker: MockerFixture
) -> None:
    repo_id = "test_finalize_state_save_failure"
    staging = tmp_path / "staged-state-failure"
    staging.mkdir()
    write_theme(staging)
    mocker.patch.object(theme_installer.ThemeState, "save", return_value=False)

    with pytest.raises(OSError, match="theme state"):
        theme_installer.finalize_install(str(staging), repo_id, INSTALL_URL, "abc", 1700000000.0)

    # The swap already happened, but the failure is reported so stale state cannot linger silently
    assert (theme_dirs.installed / repo_id).is_dir()
    assert not (theme_dirs.state / f"{repo_id}.json").exists()


def test_download__kind_changed_head_keeps_installed_theme(
    theme_dirs: SimpleNamespace, tmp_path: Path, mocker: MockerFixture
) -> None:
    repo_id = "test_download_kind_change"
    install_theme(repo_id, tmp_path / "staged-theme", css="original")
    assert (theme_dirs.installed / repo_id / "theme.css").read_text() == "original"

    class FakeSource:
        repo_id = "test_download_kind_change"
        url = INSTALL_URL

        def download(
            self,
            target_dir: str,
            on_success: Callable[[tuple[str, float]], None],
            _on_error: Callable[[Exception], None],
            _commit_hash: str | None = None,
        ) -> None:
            # The remote HEAD no longer contains a theme
            write_extension(Path(target_dir))
            on_success(("newhash", 1700000001.0))

    mocker.patch.object(theme_installer, "resolve_source", return_value=FakeSource())

    installed: list[str] = []
    errors: list[Exception] = []
    theme_installer.download(INSTALL_URL, installed.append, errors.append, "newhash")

    assert installed == []
    assert len(errors) == 1
    assert isinstance(errors[0], install_errors.InstallError)
    assert (theme_dirs.installed / repo_id / "theme.css").read_text() == "original"
    assert theme_installer.load_state(repo_id).commit_hash == "oldhash"


def test_download__failure__leaves_themes_staging_empty(theme_dirs: SimpleNamespace, mocker: MockerFixture) -> None:
    staging_root = Path(paths.THEMES_STAGING)

    class FakeSource:
        repo_id = "test_download_failure_cleanup"
        url = INSTALL_URL

        def download(
            self,
            _target_dir: str,
            _on_success: Callable[[tuple[str, float]], None],
            on_error: Callable[[Exception], None],
            _commit_hash: str | None = None,
        ) -> None:
            on_error(install_errors.InstallError("boom"))

    mocker.patch.object(theme_installer, "resolve_source", return_value=FakeSource())

    installed: list[str] = []
    errors: list[Exception] = []
    theme_installer.download(INSTALL_URL, installed.append, errors.append)

    assert installed == []
    assert len(errors) == 1
    assert list(staging_root.iterdir()) == []
    assert list(theme_dirs.installed.iterdir()) == []


@pytest.mark.usefixtures("theme_dirs")
def test_installed_ids__unreadable_root_is_empty(mocker: MockerFixture) -> None:
    mocker.patch.object(Path, "iterdir", side_effect=OSError("denied"))
    assert theme_installer.installed_ids() == []


def test_uninstall__removes_dir_and_state(theme_dirs: SimpleNamespace, tmp_path: Path) -> None:
    repo_id = "test_uninstall_theme"
    install_theme(repo_id, tmp_path / "staged-uninstall")
    assert (theme_dirs.installed / repo_id).is_dir()
    assert (theme_dirs.state / f"{repo_id}.json").is_file()
    assert repo_id in theme_installer.installed_ids()

    assert theme_installer.uninstall(repo_id) is True

    assert not (theme_dirs.installed / repo_id).exists()
    assert not (theme_dirs.state / f"{repo_id}.json").exists()
    assert repo_id not in theme_installer.installed_ids()
    assert theme_installer.uninstall(repo_id) is False


def test_uninstall__raises_when_removal_fails(
    theme_dirs: SimpleNamespace, tmp_path: Path, mocker: MockerFixture
) -> None:
    repo_id = "test_uninstall_removal_failure"
    install_theme(repo_id, tmp_path / "staged-uninstall-failure")
    mocker.patch.object(theme_installer, "rmtree", side_effect=OSError("permission denied"))

    with pytest.raises(OSError, match="permission denied"):
        theme_installer.uninstall(repo_id)

    # The removal failed, so the theme and its state must stay intact instead of reporting success
    assert (theme_dirs.installed / repo_id).is_dir()
    assert (theme_dirs.state / f"{repo_id}.json").is_file()
