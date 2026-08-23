import json
from pathlib import Path

import pytest

from ulauncher import paths
from ulauncher.ui.helpers.theme import LegacyTheme, _load_legacy_theme, get_themes


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


@pytest.fixture
def user_themes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    themes_dir = tmp_path / "user-themes"
    themes_dir.mkdir()
    monkeypatch.setattr(paths, "USER_THEMES", str(themes_dir))
    monkeypatch.setattr(paths, "SYSTEM_THEMES", str(tmp_path / "no-system-themes"))
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
