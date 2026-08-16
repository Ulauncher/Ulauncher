import json
from pathlib import Path

import pytest

from ulauncher.ui.helpers.theme import LegacyTheme, _load_legacy_theme


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
