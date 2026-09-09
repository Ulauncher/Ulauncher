import json
from pathlib import Path

import pytest

from ulauncher import paths
from ulauncher.ui.helpers.theme import LegacyTheme, Theme, _load_legacy_theme, get_theme_source, get_themes


def _write_manifest(dir_path: Path, data: object) -> Path:
    manifest_path = dir_path / "manifest.json"
    manifest_path.write_text(data if isinstance(data, str) else json.dumps(data))
    return manifest_path


def test_load_legacy_theme__valid__returns_theme(tmp_path: Path) -> None:
    manifest_path = _write_manifest(tmp_path, {"name": "dark", "css_file": "dark.css"})
    assert _load_legacy_theme(manifest_path) == LegacyTheme(name="dark", css_file="dark.css", base_path=str(tmp_path))


def test_load_legacy_theme__null_extend_theme__is_dropped(tmp_path: Path) -> None:
    theme = _load_legacy_theme(_write_manifest(tmp_path, {"name": "dark", "extend_theme": None}))
    assert theme is not None
    assert theme.extend_theme == ""


@pytest.mark.parametrize(
    "content",
    ["{not json", "5", {"name": "dark", "validate": "shadows a method"}],
    ids=["malformed_json", "not_an_object", "key_shadowing_a_method"],
)
def test_load_legacy_theme__unusable_manifest__returns_none(tmp_path: Path, content: object) -> None:
    assert _load_legacy_theme(_write_manifest(tmp_path, content)) is None


def test_load_legacy_theme__missing_file__returns_none(tmp_path: Path) -> None:
    assert _load_legacy_theme(tmp_path / "manifest.json") is None


def test_get_css__missing_file__raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Theme(name="dark", base_path=str(tmp_path)).get_css(0)


def test_legacy_get_css__missing_file__raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        LegacyTheme(name="dark", css_file="dark.css", base_path=str(tmp_path)).get_css(0)


@pytest.fixture
def user_themes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    themes_dir = tmp_path / "user-themes"
    themes_dir.mkdir()
    monkeypatch.setattr(paths, "USER_THEMES", str(themes_dir))
    monkeypatch.setattr(paths, "SYSTEM_THEMES", str(tmp_path / "no-system-themes"))
    return themes_dir


@pytest.fixture
def installed_themes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    themes_dir = tmp_path / "installed-themes"
    themes_dir.mkdir()
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(themes_dir))
    return themes_dir


def test_get_themes__manifest_in_the_user_themes_root__wins_over_the_css_glob(user_themes: Path) -> None:
    (user_themes / "dark.css").write_text("")
    _write_manifest(user_themes, {"name": "dark", "css_file": "dark.css", "extend_theme": "light"})

    theme = get_themes()["dark"]

    assert isinstance(theme, LegacyTheme)
    assert theme.extend_theme == "light"


def test_get_themes__css_the_root_manifest_does_not_describe__is_still_a_theme(user_themes: Path) -> None:
    (user_themes / "dark.css").write_text("")
    (user_themes / "blue.css").write_text("")
    _write_manifest(user_themes, {"name": "dark", "css_file": "dark.css"})

    assert sorted(get_themes()) == ["blue", "dark"]


def test_get_themes__unusable_root_manifest__leaves_the_css_themes_alone(user_themes: Path) -> None:
    (user_themes / "dark.css").write_text("")
    _write_manifest(user_themes, "{not json")

    assert sorted(get_themes()) == ["dark"]


@pytest.mark.usefixtures("user_themes")
def test_get_themes__installed_manifest__wins_over_the_css_glob(installed_themes: Path) -> None:
    repo_dir = installed_themes / "dark-repo"
    repo_dir.mkdir()
    (repo_dir / "dark.css").write_text("")
    _write_manifest(repo_dir, {"name": "dark", "css_file": "dark.css", "extend_theme": "light"})

    theme = get_themes()["dark"]

    assert isinstance(theme, LegacyTheme)
    assert theme.extend_theme == "light"


@pytest.mark.usefixtures("user_themes")
def test_get_themes__installed_manifest__hides_all_sibling_css(installed_themes: Path) -> None:
    """A manifest-owned repo never surfaces its css files (declared or stray) as standalone themes."""
    repo_dir = installed_themes / "libadwaita-repo"
    repo_dir.mkdir()
    (repo_dir / "theme.css").write_text("")
    (repo_dir / "theme-gtk-3.20.css").write_text("")
    (repo_dir / "generated.css").write_text("")
    _write_manifest(
        repo_dir, {"name": "libadwaita-dark", "css_file": "theme.css", "css_file_gtk_3.20+": "theme-gtk-3.20.css"}
    )

    assert sorted(get_themes()) == ["libadwaita-dark"]


@pytest.mark.usefixtures("user_themes")
def test_get_themes__installed_flat_css__is_still_a_theme(installed_themes: Path) -> None:
    repo_dir = installed_themes / "flat-repo"
    repo_dir.mkdir()
    (repo_dir / "flat.css").write_text("")

    assert sorted(get_themes()) == ["flat"]


def test_get_themes__root_manifest_with_both_css_files__hides_both(user_themes: Path) -> None:
    (user_themes / "theme.css").write_text("")
    (user_themes / "theme-gtk-3.20.css").write_text("")
    _write_manifest(user_themes, {"name": "dark", "css_file": "theme.css", "css_file_gtk_3.20+": "theme-gtk-3.20.css"})

    assert sorted(get_themes()) == ["dark"]


@pytest.mark.usefixtures("user_themes")
def test_get_themes__bad_installed_manifest__does_not_hide_a_good_one(installed_themes: Path) -> None:
    bad_repo = installed_themes / "bad-repo"
    bad_repo.mkdir()
    _write_manifest(bad_repo, "{not json")
    good_repo = installed_themes / "good-repo"
    good_repo.mkdir()
    (good_repo / "dark.css").write_text("")
    _write_manifest(good_repo, {"name": "dark", "css_file": "dark.css"})

    assert sorted(get_themes()) == ["dark"]


@pytest.mark.usefixtures("user_themes", "installed_themes")
def test_get_themes__staging_lookalike__is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A mid-download tree in staging is never surfaced as an installed theme."""
    # Deferred like get_themes() does, so importing this module never pulls in the extension stack
    from ulauncher.internals import theme_installer

    for attr in ("THEMES_STAGING", "PENDING_STAGING"):
        repo = tmp_path / attr / "half-downloaded"
        repo.mkdir(parents=True)
        (repo / "dark.css").write_text("")
        _write_manifest(repo, {"name": "dark", "css_file": "dark.css"})
        monkeypatch.setattr(paths, attr, str(tmp_path / attr))

    assert theme_installer.installed_ids() == []
    assert "dark" not in get_themes()


def test_get_themes__installed_themes__show_up_alongside_user_and_system_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_dir = tmp_path / "user-themes"
    user_dir.mkdir()
    (user_dir / "user.css").write_text("")
    system_dir = tmp_path / "system-themes"
    system_dir.mkdir()
    (system_dir / "system.css").write_text("")
    installed_dir = tmp_path / "installed-themes"
    repo_dir = installed_dir / "repo"
    repo_dir.mkdir(parents=True)
    (repo_dir / "installed.css").write_text("")
    monkeypatch.setattr(paths, "USER_THEMES", str(user_dir))
    monkeypatch.setattr(paths, "SYSTEM_THEMES", str(system_dir))
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(installed_dir))

    assert sorted(get_themes()) == ["installed", "system", "user"]


def _install_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repo_id: str, url: str) -> Path:
    installed = tmp_path / "installed-themes"
    state = tmp_path / "theme-state"
    repo_dir = installed / repo_id
    repo_dir.mkdir(parents=True)
    state.mkdir()
    (state / f"{repo_id}.json").write_text(json.dumps({"url": url}))
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(installed))
    monkeypatch.setattr(paths, "THEMES_STATE", str(state))
    return repo_dir


def test_get_theme_source__installed_theme__returns_owner_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_dir = _install_state(
        tmp_path,
        monkeypatch,
        "com.github.heidefinnischen.ulauncher-elementary_flat",
        "https://github.com/heidefinnischen/ULauncher-elementary_Flat",
    )

    theme = Theme(name="Odin Dark", base_path=str(repo_dir))
    assert get_theme_source(theme) == "heidefinnischen/ULauncher-elementary_Flat"


def test_get_theme_source__nested_variant__returns_owner_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_dir = _install_state(tmp_path, monkeypatch, "com.github.owner.repo", "https://github.com/owner/repo")

    theme = Theme(name="dark", base_path=str(repo_dir / "variants" / "dark"))
    assert get_theme_source(theme) == "owner/repo"


def test_get_theme_source__user_theme__returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "INSTALLED_THEMES", str(tmp_path / "installed-themes"))

    theme = Theme(name="dark", base_path=str(tmp_path / "user-themes" / "dark"))
    assert get_theme_source(theme) is None


def test_get_theme_source__local_install__returns_none(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_dir = _install_state(tmp_path, monkeypatch, "local.repo", f"file://{tmp_path}")

    assert get_theme_source(Theme(name="dark", base_path=str(repo_dir))) is None
